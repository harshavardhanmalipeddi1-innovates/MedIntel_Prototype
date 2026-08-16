# Portable inference for the synthetic DDXPlus XGBoost v6.2 package.
# This program is not clinically validated. It does not diagnose emergencies,
# recommend treatment, or generate prescriptions.
from pathlib import Path
import json
import joblib
import numpy as np
from scipy import sparse
import xgboost as xgb

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "respiratory"
MODEL_DIR = ARTIFACT_DIR / "model"
bundle = joblib.load(
    ARTIFACT_DIR / "preprocessing" / "preprocessing_bundle.joblib"
)
with open(
    ARTIFACT_DIR / "metadata" / "portable_metadata.json",
    "r",
    encoding="utf-8",
) as file:
    metadata = json.load(file)

primary_model = xgb.XGBClassifier()
primary_model.load_model(MODEL_DIR / metadata["primary_model_file"])

scope_model = xgb.XGBClassifier()
scope_model.load_model(MODEL_DIR / metadata["scope_model_file"])


ddx_models = {}
for condition, relative_path in metadata["ddx_model_files"].items():
    model_path = MODEL_DIR / relative_path
    if model_path.is_file():
        model = xgb.XGBRegressor()
        model.load_model(model_path)
        ddx_models[condition] = model

inclusion_models = {}
for condition, relative_path in metadata["inclusion_model_files"].items():
    model_path = MODEL_DIR / relative_path
    if model_path.is_file():
        model = xgb.XGBClassifier()
        model.load_model(model_path)
        inclusion_models[condition] = model

critical_head_models = {}
for condition, relative_path in metadata["critical_head_model_files"].items():
    model_path = MODEL_DIR / relative_path
    if model_path.is_file():
        model = xgb.XGBClassifier()
        model.load_model(model_path)
        critical_head_models[condition] = model

CLASS_NAMES = bundle["class_names"]
CLASS_TO_INDEX = {
    name: index
    for index, name in enumerate(CLASS_NAMES)
}
EPS = 1e-12


def evidence_base_code(code):
    return str(code).split("_@_", 1)[0]


def questionnaire_completion_fraction(
    answered_question_codes,
    eligible_question_codes,
):
    answered = {
        evidence_base_code(code)
        for code in answered_question_codes
    }
    eligible = {
        evidence_base_code(code)
        for code in eligible_question_codes
    }
    if not eligible:
        raise ValueError(
            "eligible_question_codes must contain at least one item."
        )
    answered_count = len(answered & eligible)
    return float(answered_count / len(eligible)), int(answered_count)


def stage_code(completion_fraction):
    if completion_fraction <= 0:
        return 0.0
    if completion_fraction < 0.5:
        return 1.0
    if completion_fraction < 1.0:
        return 2.0
    return 3.0


def dense_matrix(
    age,
    sex,
    positive_evidence_count,
    completion_fraction,
):
    sex_value = {
        "F": 0.0,
        "M": 1.0,
    }.get(str(sex).upper(), -1.0)
    values = np.array([[
        float(age),
        sex_value,
        float(positive_evidence_count),
        float(completion_fraction),
        float(positive_evidence_count <= 0),
        stage_code(float(completion_fraction)),
    ]], dtype=np.float32)
    return sparse.csr_matrix(values)


def respiratory_matrix(
    age,
    sex,
    evidence_codes,
    initial_evidence,
    completion_fraction,
):
    tokens = sorted(set(
        [str(code) for code in evidence_codes]
        + [f"INITIAL::{initial_evidence}"]
    ))
    encoded = bundle["evidence_encoder"].transform([tokens])
    return sparse.hstack([
        dense_matrix(
            age,
            sex,
            len(set(evidence_codes)),
            completion_fraction,
        ),
        encoded,
    ], format="csr", dtype=np.float32)


def scope_matrix(
    age,
    sex,
    evidence_codes,
    initial_evidence,
    completion_fraction,
):
    text = (
        " ".join(str(code) for code in evidence_codes)
        + " INITIAL__"
        + str(initial_evidence)
    )
    encoded = bundle["scope_vectorizer"].transform(
        [text]
    ).astype(np.float32)
    return sparse.hstack([
        dense_matrix(
            age,
            sex,
            len(set(evidence_codes)),
            completion_fraction,
        ),
        encoded,
    ], format="csr", dtype=np.float32)


def temperature_scale(probabilities, temperature):
    probabilities = np.clip(probabilities, EPS, 1.0)
    logits = np.log(probabilities) / float(temperature)
    logits -= logits.max(axis=1, keepdims=True)
    exp_values = np.exp(logits)
    return exp_values / exp_values.sum(
        axis=1,
        keepdims=True,
    )


def binary_temperature_scale(probability, temperature):
    probability = np.clip(
        probability,
        EPS,
        1.0 - EPS,
    )
    logit = np.log(
        probability / (1.0 - probability)
    ) / float(temperature)
    return float(1.0 / (1.0 + np.exp(-logit)))


def nearest_bucket(completion_fraction):
    return min(
        bundle["evaluation_retention_levels"],
        key=lambda value: abs(
            float(value) - float(completion_fraction)
        ),
    )


def nearest_scope_bucket(completion_fraction):
    return min(
        bundle["scope_thresholds_by_level"],
        key=lambda value: abs(
            float(value) - float(completion_fraction)
        ),
    )


def metadata_question(base_code):
    details = bundle.get(
        "evidence_metadata",
        {},
    ).get(base_code, {})
    if not isinstance(details, dict):
        return None
    for key in (
        "question_en",
        "question",
        "name_en",
        "name",
        "description_en",
        "description",
    ):
        value = details.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def suggest_next_questions(
    observed_evidence_codes,
    ddx_scores,
    question_count=5,
    top_candidate_count=5,
):
    prevalence = np.asarray(
        bundle["class_evidence_prevalence"],
        dtype=np.float32,
    )
    question_groups = bundle["question_groups"]
    observed_bases = {
        evidence_base_code(code)
        for code in observed_evidence_codes
    }
    scores = np.asarray(ddx_scores, dtype=np.float64)
    top_indices = np.argsort(scores)[::-1][
        :min(top_candidate_count, len(CLASS_NAMES))
    ]
    weights = scores[top_indices]
    if weights.sum() <= 0:
        weights = np.ones(
            len(top_indices),
            dtype=np.float64,
        )
    weights = weights / weights.sum()

    rows = []
    for base_code, column_indices in question_groups.items():
        if base_code in observed_bases:
            continue
        candidate_prevalence = prevalence[
            np.ix_(top_indices, column_indices)
        ]
        weighted_mean = np.sum(
            weights[:, None] * candidate_prevalence,
            axis=0,
        )
        weighted_variance = np.sum(
            weights[:, None]
            * (
                candidate_prevalence
                - weighted_mean[None, :]
            ) ** 2,
            axis=0,
        )
        disagreement = float(
            weighted_variance.max(initial=0.0)
        )
        if disagreement <= 0:
            continue
        rows.append({
            "evidence_code": base_code,
            "candidate_disagreement_score": disagreement,
            "question": metadata_question(base_code),
        })
    rows.sort(
        key=lambda item: item[
            "candidate_disagreement_score"
        ],
        reverse=True,
    )
    return rows[:int(question_count)]


def base_ddx_scores(matrix, primary):
    scores_list = []
    for condition in CLASS_NAMES:
        if condition in ddx_models:
            score = max(0.0, float(ddx_models[condition].predict(matrix)[0]))
        else:
            score = 0.0
        scores_list.append(score)
    scores = np.array(scores_list, dtype=np.float32)
    if scores.sum() > 0:
        return scores / scores.sum()
    return primary.copy()


def inclusion_scores(matrix, bucket):
    output = {}
    for condition, model in inclusion_models.items():
        raw = float(model.predict_proba(matrix)[0, 1])
        temperature = bundle[
            "inclusion_temperatures_by_level"
        ][condition][bucket]
        output[condition] = binary_temperature_scale(
            raw,
            temperature,
        )
    return output


def critical_considerations(
    base_scores,
    inclusion,
    bucket,
    top_k,
):
    base_order = np.argsort(base_scores)[::-1]
    base_topk = base_order[:top_k]
    thresholds = bundle[
        "critical_consideration_thresholds_by_level"
    ][bucket]
    eligible = []
    for condition in bundle[
        "critical_consideration_target_conditions"
    ]:
        class_index = CLASS_TO_INDEX[condition]
        if class_index in base_topk:
            continue
        threshold = float(thresholds[condition])
        probability = float(inclusion[condition])
        if probability < threshold:
            continue
        margin = (
            probability - threshold
        ) / max(1.0 - threshold, 1e-6)
        eligible.append((margin, probability, condition))

    eligible.sort(reverse=True)
    maximum = int(
        bundle["max_critical_considerations_per_case"]
    )
    return [
        {
            "condition": condition,
            "candidate_inclusion_score": float(probability),
            "validation_threshold": float(thresholds[condition]),
            "normalized_margin": float(margin),
            "separate_from_ranked_top5": True,
        }
        for margin, probability, condition
        in eligible[:maximum]
    ]

def critical_pathology_signals(matrix, bucket):
    rows = []
    thresholds = bundle[
        "critical_head_thresholds_by_level"
    ]
    for condition, model in critical_head_models.items():
        score = float(model.predict_proba(matrix)[0, 1])
        threshold = float(thresholds[condition][bucket])
        rows.append({
            "condition": condition,
            "critical_pathology_score": score,
            "signal_threshold": threshold,
            "signal": bool(score >= threshold),
            "research_only": True,
        })
    rows.sort(
        key=lambda item: item["critical_pathology_score"],
        reverse=True,
    )
    return rows


def predict(
    age,
    sex,
    evidence_codes,
    initial_evidence,
    answered_question_codes,
    eligible_question_codes,
    top_k=5,
):
    evidence_codes = [str(code) for code in evidence_codes]
    initial_evidence = str(initial_evidence)
    completion_fraction, answered_count = (
        questionnaire_completion_fraction(
            answered_question_codes,
            eligible_question_codes,
        )
    )
    bucket = nearest_bucket(completion_fraction)

    s_matrix = scope_matrix(
        age,
        sex,
        evidence_codes,
        initial_evidence,
        completion_fraction,
    )
    scope_score = float(
        scope_model.predict_proba(s_matrix)[0, 1]
    )
    scope_bucket = nearest_scope_bucket(completion_fraction)
    thresholds = bundle[
        "scope_thresholds_by_level"
    ][scope_bucket]
    policy = bundle["scope_policy_config"]
    direct_allowed = (
        completion_fraction
        >= policy["minimum_completion_for_direct_decision"]
        and answered_count
        >= policy["minimum_information_items_for_direct_decision"]
    )
    if not direct_allowed:
        state = "INSUFFICIENT_INFORMATION"
    elif scope_score >= thresholds["supported_threshold"]:
        state = "SUPPORTED_SCOPE"
    elif scope_score <= thresholds["unsupported_threshold"]:
        state = "UNSUPPORTED_SCOPE"
    else:
        state = "INSUFFICIENT_INFORMATION"

    r_matrix = respiratory_matrix(
        age,
        sex,
        evidence_codes,
        initial_evidence,
        completion_fraction,
    )
    primary_raw = primary_model.predict_proba(r_matrix)
    primary = temperature_scale(
        primary_raw,
        bundle["primary_temperatures"][bucket],
    )[0]
    primary_confidence_accepted = bool(
        primary.max()
        >= bundle["primary_confidence_thresholds"][bucket]
    )
    base = base_ddx_scores(r_matrix, primary)
    inclusion = inclusion_scores(r_matrix, bucket)
    signals = critical_pathology_signals(r_matrix, bucket)
    positive_signals = [row for row in signals if row["signal"]]

    if state == "INSUFFICIENT_INFORMATION":
        return {
            "status": state,
            "completion_fraction": completion_fraction,
            "scope_supported_score": scope_score,
            "primary_confidence_accepted": primary_confidence_accepted,
            "next_questions": suggest_next_questions(
                list(answered_question_codes) + [initial_evidence],
                base,
                question_count=5,
            ),
            "candidates": [],
            "possible_critical_pathology_signals": positive_signals,
            "research_warning": (
                "Critical-pathology signals are synthetic label "
                "predictions, not emergency or severity decisions."
            ),
        }

    if state == "UNSUPPORTED_SCOPE":
        return {
            "status": state,
            "completion_fraction": completion_fraction,
            "scope_supported_score": scope_score,
            "primary_confidence_accepted": primary_confidence_accepted,
            "next_questions": [],
            "candidates": [],
            "possible_critical_pathology_signals": [],
        }

    order = np.argsort(base)[::-1][
        :min(int(top_k), len(CLASS_NAMES))
    ]
    candidates = [
        {
            "rank": rank,
            "condition": CLASS_NAMES[int(index)],
            "base_ddx_relevance_score": float(base[index]),
            "primary_model_confidence": float(primary[index]),
        }
        for rank, index in enumerate(order, start=1)
    ]
    considerations = critical_considerations(
        base,
        inclusion,
        bucket,
        min(int(top_k), len(CLASS_NAMES)),
    )
    return {
        "status": state,
        "completion_fraction": completion_fraction,
        "scope_supported_score": scope_score,
        "primary_confidence_accepted": primary_confidence_accepted,
        "next_questions": [],
        "candidates": candidates,
        "additional_critical_considerations": considerations,
        "possible_critical_pathology_signals": positive_signals,
    }
