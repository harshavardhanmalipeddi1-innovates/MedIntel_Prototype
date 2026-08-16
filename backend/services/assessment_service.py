import json
from pathlib import Path
from typing import Any

from backend.app.ml.feature_builder import FeatureBuilder


class AssessmentService:
    """Translate doctor-facing assessment answers into the deployed model contract.

    Eligibility baseline:
    The active Phase 5 questionnaire is the complete model-scoped questionnaire,
    excluding the already-known initial evidence. The trained portable inference
    accepts eligible question codes as an external contract and does not contain
    a complete dependency engine. We therefore do not invent eligibility from
    DDXPlus code_question metadata.
    """

    def __init__(
        self,
        metadata_path: Path | None = None,
        feature_builder: FeatureBuilder | None = None,
    ) -> None:
        backend_root = Path(__file__).resolve().parents[1]
        self._metadata_path = metadata_path or (
            backend_root
            / "models"
            / "respiratory"
            / "metadata"
            / "ddxplus_evidence_metadata.json"
        )
        self._feature_builder = feature_builder or FeatureBuilder()
        self._metadata: dict[str, Any] | None = None

    def _load_metadata(self) -> dict[str, Any]:
        if self._metadata is None:
            with self._metadata_path.open("r", encoding="utf-8-sig") as file:
                metadata = json.load(file)

            if not isinstance(metadata.get("evidences"), dict):
                raise RuntimeError(
                    "DDXPlus evidence metadata is missing or invalid."
                )

            model_scope = metadata.get("model_scope", {})
            base_codes = model_scope.get("base_evidence_codes", [])

            if not isinstance(base_codes, list) or len(base_codes) != 85:
                raise RuntimeError(
                    "Expected 85 model-scoped evidence definitions."
                )

            self._metadata = metadata

        return self._metadata

    def _encoder_classes(self) -> list[str]:
        bundle = self._feature_builder.preprocessing_bundle

        if isinstance(bundle, dict):
            encoder = bundle["evidence_encoder"]
        else:
            encoder = bundle.evidence_encoder

        return [str(value) for value in encoder.classes_]

    def _encoder_class_set(self) -> set[str]:
        return set(self._encoder_classes())

    def _base_codes(self) -> list[str]:
        metadata = self._load_metadata()
        return [
            str(code)
            for code in metadata["model_scope"]["base_evidence_codes"]
        ]

    def _initial_evidence_codes(self) -> set[str]:
        return {
            token.removeprefix("INITIAL::")
            for token in self._encoder_classes()
            if token.startswith("INITIAL::")
        }

    def _evidence_details(self, code: str) -> dict[str, Any]:
        metadata = self._load_metadata()
        details = metadata["evidences"].get(code)

        if not isinstance(details, dict):
            raise ValueError(f"Unknown assessment evidence code: {code}")

        return details

    @staticmethod
    def _possible_values(details: dict[str, Any]) -> list[str]:
        possible = (
            details.get("possible-values")
            or details.get("possible_values")
            or details.get("values")
            or []
        )

        if isinstance(possible, dict):
            return [str(value) for value in possible.keys()]

        if isinstance(possible, list):
            return [str(value) for value in possible]

        return []

    @staticmethod
    def _value_label(details: dict[str, Any], value: str) -> str:
        meanings = details.get("value_meaning") or {}

        if isinstance(meanings, dict):
            meaning = meanings.get(value)

            if isinstance(meaning, dict):
                english = meaning.get("en")
                if isinstance(english, str) and english.strip():
                    return english.strip()

            if isinstance(meaning, str) and meaning.strip():
                return meaning.strip()

        return value

    def _supported_values(
        self,
        code: str,
        details: dict[str, Any],
    ) -> list[str]:
        """Return values this deployed encoder can represent.

        The metadata default is also retained as a valid no-token answer when
        the encoder does not contain a dedicated token for that default.
        """
        possible_values = self._possible_values(details)
        encoder_classes = self._encoder_class_set()

        supported = [
            value
            for value in possible_values
            if f"{code}_@_{value}" in encoder_classes
        ]

        default_value = details.get("default_value")

        if default_value is not None:
            default_text = str(default_value)

            if (
                default_text in possible_values
                and default_text not in supported
            ):
                supported.append(default_text)

        return [
            value
            for value in possible_values
            if value in set(supported)
        ]

    @staticmethod
    def _is_numeric_scale(
        data_type: str,
        values: list[str],
        details: dict[str, Any],
    ) -> bool:
        if data_type != "C" or not values:
            return False

        # The six numeric DDXPlus scale questions have numeric values and no
        # human value_meaning map. Model-scoped supported values determine the
        # actual scale range exposed by this deployment.
        if details.get("value_meaning"):
            return False

        try:
            [int(value) for value in values]
        except (TypeError, ValueError):
            return False

        return True

    def _build_question(
        self,
        code: str,
        details: dict[str, Any],
        initial_codes: set[str],
    ) -> dict[str, Any]:
        question = details.get("question_en")

        if not isinstance(question, str) or not question.strip():
            raise RuntimeError(
                f"Human-readable question missing for evidence {code}."
            )

        data_type = str(details.get("data_type", "")).upper()
        options: list[dict[str, str]] = []
        scale_min = None
        scale_max = None

        if data_type == "B":
            answer_kind = "binary"
            options = [
                {"value": "true", "label": "Yes"},
                {"value": "false", "label": "No"},
            ]
        elif data_type in {"C", "M"}:
            supported_values = self._supported_values(code, details)

            if not supported_values:
                raise RuntimeError(
                    f"No model-supported values available for evidence {code}."
                )

            if self._is_numeric_scale(
                data_type,
                supported_values,
                details,
            ):
                answer_kind = "scale"
                numeric_values = [int(value) for value in supported_values]
                scale_min = min(numeric_values)
                scale_max = max(numeric_values)
            else:
                answer_kind = (
                    "single_select"
                    if data_type == "C"
                    else "multi_select"
                )
                options = [
                    {
                        "value": value,
                        "label": self._value_label(details, value),
                    }
                    for value in supported_values
                ]
        else:
            raise RuntimeError(
                f"Unsupported DDXPlus data type {data_type!r} "
                f"for evidence {code}."
            )

        return {
            "code": code,
            "question": question.strip(),
            "data_type": data_type,
            "answer_kind": answer_kind,
            "is_antecedent": bool(details.get("is_antecedent", False)),
            "initial_evidence_allowed": code in initial_codes,
            "default_value": details.get("default_value"),
            "options": options,
            "scale_min": scale_min,
            "scale_max": scale_max,
        }

    def get_questionnaire(self) -> dict[str, Any]:
        metadata = self._load_metadata()
        evidences = metadata["evidences"]
        base_codes = self._base_codes()
        initial_codes = self._initial_evidence_codes()
        questions = []

        for code in base_codes:
            details = evidences.get(code)

            if not isinstance(details, dict):
                raise RuntimeError(
                    f"Metadata missing for evidence {code}."
                )

            questions.append(
                self._build_question(code, details, initial_codes)
            )

        return {
            "version": "ddxplus-model-scope-v1",
            "question_count": len(questions),
            "initial_evidence_count": len(initial_codes),
            "initial_evidence_codes": sorted(initial_codes),
            "questions": questions,
            "source": metadata.get("source", {}),
        }

    @staticmethod
    def _normalize_binary(value: Any, code: str) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized == "true":
                return True

            if normalized == "false":
                return False

        raise ValueError(
            f"Binary evidence {code} requires true or false."
        )

    def _answer_tokens(
        self,
        code: str,
        value: Any,
    ) -> list[str]:
        details = self._evidence_details(code)
        data_type = str(details.get("data_type", "")).upper()
        encoder_classes = self._encoder_class_set()

        if data_type == "B":
            if not self._normalize_binary(value, code):
                return []

            if code not in encoder_classes:
                raise ValueError(
                    f"Positive evidence {code} is not represented by "
                    "the deployed model encoder."
                )

            return [code]

        supported_values = self._supported_values(code, details)
        default_value = details.get("default_value")
        default_text = (
            str(default_value)
            if default_value is not None
            else None
        )

        if data_type == "C":
            normalized = str(value)

            if normalized not in supported_values:
                raise ValueError(
                    f"Unsupported value {normalized!r} for evidence {code}."
                )

            token = f"{code}_@_{normalized}"

            if token in encoder_classes:
                return [token]

            if default_text == normalized:
                return []

            raise ValueError(
                f"Evidence value {normalized!r} for {code} cannot be "
                "represented by the deployed model encoder."
            )

        if data_type == "M":
            if not isinstance(value, list):
                raise ValueError(
                    f"Multi-choice evidence {code} requires a list."
                )

            normalized_values = [str(item) for item in value]

            if len(normalized_values) != len(set(normalized_values)):
                raise ValueError(
                    f"Duplicate values supplied for evidence {code}."
                )

            invalid = [
                item
                for item in normalized_values
                if item not in supported_values
            ]

            if invalid:
                raise ValueError(
                    f"Unsupported value(s) for evidence {code}: "
                    f"{', '.join(invalid)}"
                )

            if (
                default_text is not None
                and default_text in normalized_values
                and len(normalized_values) > 1
            ):
                raise ValueError(
                    f"Default value for evidence {code} cannot be "
                    "combined with other selections."
                )

            tokens = []

            for item in normalized_values:
                token = f"{code}_@_{item}"

                if token in encoder_classes:
                    tokens.append(token)
                    continue

                if default_text == item:
                    continue

                raise ValueError(
                    f"Evidence value {item!r} for {code} cannot be "
                    "represented by the deployed model encoder."
                )

            return tokens

        raise ValueError(
            f"Unsupported DDXPlus data type {data_type!r} "
            f"for evidence {code}."
        )

    @staticmethod
    def _stage_code(completion_fraction: float) -> float:
        if completion_fraction <= 0:
            return 0.0

        if completion_fraction < 0.5:
            return 1.0

        if completion_fraction < 1.0:
            return 2.0

        return 3.0

    def prepare_assessment(
        self,
        *,
        age: int,
        sex: str,
        initial_evidence: str,
        answers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        initial_codes = self._initial_evidence_codes()

        if initial_evidence not in initial_codes:
            raise ValueError(
                f"Evidence {initial_evidence} is not a valid initial "
                "evidence for this deployed model."
            )

        encoder_classes = self._encoder_class_set()
        initial_token = f"INITIAL::{initial_evidence}"

        if initial_token not in encoder_classes:
            raise RuntimeError(
                f"Initial evidence token {initial_token} is absent "
                "from the deployed encoder."
            )

        eligible_codes = set(self._base_codes()) - {initial_evidence}

        if not eligible_codes:
            raise RuntimeError(
                "The model-scoped questionnaire contains no non-initial "
                "questions."
            )

        seen_codes: set[str] = set()
        positive_tokens: list[str] = []

        for answer in answers:
            code = str(answer.get("code", "")).strip()

            if not code:
                raise ValueError("Assessment answer code cannot be empty.")

            if code == initial_evidence:
                raise ValueError(
                    "The initial evidence is already known and must not "
                    "also be submitted as a questionnaire answer."
                )

            if code not in eligible_codes:
                raise ValueError(
                    f"Evidence {code} is not eligible in the active "
                    "model-scoped questionnaire."
                )

            if code in seen_codes:
                raise ValueError(
                    f"Duplicate answer supplied for evidence {code}."
                )

            seen_codes.add(code)
            positive_tokens.extend(
                self._answer_tokens(
                    code,
                    answer.get("value"),
                )
            )

        positive_tokens = sorted(set(positive_tokens))

        unknown_tokens = [
            token
            for token in positive_tokens
            if token not in encoder_classes
        ]

        if unknown_tokens:
            raise RuntimeError(
                "Answer translation produced token(s) not present in the "
                "deployed model encoder: "
                + ", ".join(unknown_tokens)
            )

        answered_codes = sorted(seen_codes)
        eligible_codes_sorted = sorted(eligible_codes)
        answered_count = len(seen_codes)
        eligible_count = len(eligible_codes)

        completion_fraction = float(
            answered_count / eligible_count
        )

        positive_count = len(positive_tokens)

        model_tokens = sorted(
            set(positive_tokens + [initial_token])
        )

        patient_context = {
            "AGE": int(age),
            "SEX_MALE_CODE": 1.0 if sex == "M" else 0.0,
            "NONINITIAL_EVIDENCE_COUNT": positive_count,
            "QUESTIONNAIRE_COMPLETION_FRACTION": completion_fraction,
            "INITIAL_EVIDENCE_ONLY": float(positive_count <= 0),
            "CONSULTATION_STAGE_CODE": self._stage_code(
                completion_fraction
            ),
            "evidence_tokens": model_tokens,
            "age": int(age),
            "sex": sex,
            "initial_evidence": initial_evidence,
            "positive_evidence_tokens": positive_tokens,
            "answered_question_codes": answered_codes,
            "eligible_question_codes": eligible_codes_sorted,
        }

        # Final compatibility check against the already-validated model adapter.
        self._feature_builder.build_feature_vector(patient_context)

        return {
            "patient_context": patient_context,
            "initial_evidence": initial_evidence,
            "positive_evidence_tokens": positive_tokens,
            "answered_question_codes": answered_codes,
            "eligible_question_codes": eligible_codes_sorted,
            "answered_question_count": answered_count,
            "eligible_question_count": eligible_count,
            "questionnaire_completion_fraction": completion_fraction,
        }
