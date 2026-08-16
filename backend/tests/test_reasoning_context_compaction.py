import json

from backend.app.modules.reasoning_engine.context_builder import (
    ContextBuilder,
)
from backend.app.schemas.knowledge_schema import (
    ClinicalReference,
    DiseaseKnowledge,
)
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalRuleResult,
    ReasoningDifferentialItem,
)


def _knowledge() -> DiseaseKnowledge:
    return DiseaseKnowledge(
        disease_id="pneumonia",
        name="Pneumonia",
        aliases=["Synthetic alias"],
        description=(
            "Synthetic generic disease description that should not "
            "be duplicated into the bounded reasoning context."
        ),
        body_system="Respiratory",
        common_symptoms=[
            "Cough",
            "Fever",
            "Dyspnea",
            "Fatigue",
            "Fifth symptom",
        ],
        associated_symptoms=[
            "Associated 1",
            "Associated 2",
            "Associated 3",
            "Associated 4",
        ],
        risk_factors=[
            "Risk 1",
            "Risk 2",
            "Risk 3",
            "Risk 4",
            "Risk 5",
        ],
        physical_examination=[
            "Exam 1",
            "Exam 2",
            "Exam 3",
            "Exam 4",
        ],
        recommended_investigations=[
            "Investigation 1",
            "Investigation 2",
            "Investigation 3",
            "Investigation 4",
        ],
        red_flags=[
            "Red flag 1",
            "Red flag 2",
            "Red flag 3",
            "Red flag 4",
            "Red flag 5",
        ],
        contraindications=[
            "Synthetic treatment contraindication",
        ],
        differential_diagnoses=[
            "Asthma",
        ],
        icd10_codes=[
            "J18.9",
        ],
        clinical_references=[
            ClinicalReference(
                title="Synthetic reference",
                organization="Synthetic organization",
                year="2026",
                url="https://example.invalid/reference",
            )
        ],
        knowledge_version="test-v1",
    )


def _request() -> ClinicalReasoningRequest:
    return ClinicalReasoningRequest(
        patient_context={
            # ML / questionnaire bookkeeping: model-facing copy
            # should omit these.
            "AGE": 45,
            "SEX_MALE_CODE": 1.0,
            "NONINITIAL_EVIDENCE_COUNT": 1,
            "QUESTIONNAIRE_COMPLETION_FRACTION": 0.25,
            "INITIAL_EVIDENCE_ONLY": 0.0,
            "CONSULTATION_STAGE_CODE": 1.0,
            "eligible_question_codes": [
                "E_1",
                "E_2",
                "E_3",
            ],

            # Actual clinical/context fields must survive.
            "age": 45,
            "sex": "M",
            "initial_evidence": "E_201",
            "positive_evidence_tokens": [
                "E_77",
            ],
            "answered_question_codes": [
                "E_45",
                "E_77",
            ],
            "evidence_tokens": [
                "E_77",
                "INITIAL::E_201",
            ],

            # Future arbitrary clinical information must not be lost.
            "temperature_c": 38.1,
            "clinician_note": "Synthetic clinical context.",
        },
        rules=ClinicalRuleResult(
            alerts=[
                "Synthetic respiratory review alert",
            ],
            status="evaluated",
        ),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Pneumonia",
                probability=0.82,
                confidence="High",
                knowledge=_knowledge(),
            )
        ],
    )


def test_patient_context_removes_only_bookkeeping_fields():
    request = _request()

    payload = json.loads(
        ContextBuilder.build_context(
            request
        )
    )

    patient = payload[
        "Patient_Context"
    ]

    for key in {
        "AGE",
        "SEX_MALE_CODE",
        "NONINITIAL_EVIDENCE_COUNT",
        "QUESTIONNAIRE_COMPLETION_FRACTION",
        "INITIAL_EVIDENCE_ONLY",
        "CONSULTATION_STAGE_CODE",
        "eligible_question_codes",
    }:
        assert key not in patient

    assert patient["age"] == 45
    assert patient["sex"] == "M"
    assert patient["initial_evidence"] == "E_201"
    assert patient["positive_evidence_tokens"] == ["E_77"]
    assert patient["answered_question_codes"] == [
        "E_45",
        "E_77",
    ]
    assert patient["evidence_tokens"] == [
        "E_77",
        "INITIAL::E_201",
    ]

    # Arbitrary future clinical fields remain model-visible.
    assert patient["temperature_c"] == 38.1
    assert (
        patient["clinician_note"]
        == "Synthetic clinical context."
    )

    # Original request is untouched.
    assert request.patient_context["AGE"] == 45
    assert (
        request.patient_context["eligible_question_codes"]
        == ["E_1", "E_2", "E_3"]
    )


def test_reasoning_knowledge_is_bounded_clinical_projection():
    request = _request()

    payload = json.loads(
        ContextBuilder.build_context(
            request
        )
    )

    knowledge = payload[
        "Ranked_Differential_Candidates"
    ][0]["Knowledge"]

    assert set(knowledge) == {
        "common_symptoms",
        "associated_symptoms",
        "risk_factors",
        "physical_examination",
        "recommended_investigations",
        "red_flags",
    }

    assert len(
        knowledge["common_symptoms"]
    ) == 4

    assert len(
        knowledge["associated_symptoms"]
    ) == 3

    assert len(
        knowledge["risk_factors"]
    ) == 4

    assert len(
        knowledge["physical_examination"]
    ) == 3

    assert len(
        knowledge["recommended_investigations"]
    ) == 3

    assert len(
        knowledge["red_flags"]
    ) == 4

    assert "description" not in knowledge
    assert "contraindications" not in knowledge
    assert "aliases" not in knowledge
    assert "body_system" not in knowledge
    assert "differential_diagnoses" not in knowledge
    assert "icd10_codes" not in knowledge
    assert "clinical_references" not in knowledge
    assert "knowledge_version" not in knowledge

    # Full source KB remains unchanged.
    original = request.differential[0].knowledge

    assert original is not None
    assert len(original.common_symptoms) == 5
    assert len(original.red_flags) == 5
    assert len(original.recommended_investigations) == 4
    assert original.description
    assert original.contraindications
    assert original.icd10_codes == ["J18.9"]
    assert original.knowledge_version == "test-v1"


def test_context_builder_preserves_candidate_identity():
    payload = json.loads(
        ContextBuilder.build_context(
            _request()
        )
    )

    candidate = payload[
        "Ranked_Differential_Candidates"
    ][0]

    assert candidate["Rank"] == 1
    assert candidate["Disease"] == "Pneumonia"
    assert candidate["Probability"] == 0.82
    assert candidate["Confidence"] == "High"
    assert candidate["Knowledge_Available"] is True


def test_semantic_evidence_context_remains_present():
    payload = json.loads(
        ContextBuilder.build_context(
            _request()
        )
    )

    semantic = payload[
        "Semantic_Evidence_Context"
    ]

    assert "Observed_Clinical_Evidence" in semantic
    assert (
        "Explicitly_Answered_Question_Codes"
        in semantic
    )
    assert "Evidence_Interpretation" in semantic


def test_context_builder_uses_minified_json():
    context = ContextBuilder.build_context(
        _request()
    )

    decoded = json.loads(
        context
    )

    assert context == json.dumps(
        decoded,
        ensure_ascii=False,
        separators=(",", ":"),
    )