from backend.app.modules.reasoning_engine.evidence_semantic_normalizer import (
    EvidenceSemanticNormalizer,
)
from backend.app.schemas.reasoning_schema import (
    CandidateReasoning,
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
    ClinicalRuleResult,
    ReasoningDifferentialItem,
)


def _request() -> ClinicalReasoningRequest:
    return ClinicalReasoningRequest(
        patient_context={
            "initial_evidence": "E_77",
            "positive_evidence_tokens": [
                "E_31",
                "E_66",
            ],
            "answered_question_codes": [
                "E_31",
                "E_66",
                "E_72",
            ],
            "evidence_tokens": [
                "E_31",
                "E_66",
                "INITIAL::E_77",
            ],
        },
        rules=ClinicalRuleResult(),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Bronchiectasis",
                probability=0.4,
                confidence="Low",
            )
        ],
    )


def _response(
    *,
    supporting=None,
    conflicting=None,
    missing=None,
) -> ClinicalReasoningResponse:
    return ClinicalReasoningResponse(
        candidate_reasoning=[
            CandidateReasoning(
                rank=1,
                disease="Bronchiectasis",
                supporting_findings=(
                    supporting or []
                ),
                conflicting_findings=(
                    conflicting or []
                ),
                missing_information=(
                    missing or []
                ),
                rationale=(
                    "Findings are compatible with "
                    "consideration of this candidate."
                ),
            )
        ],
        reasoning_summary=(
            "Clinician verification is required."
        ),
        requires_doctor_review=True,
    )


def test_raw_supporting_codes_become_human_readable():
    result = EvidenceSemanticNormalizer.normalize(
        _request(),
        _response(
            supporting=[
                "E_31",
                "E_66",
                "E_77",
            ]
        ),
    )

    findings = (
        result
        .candidate_reasoning[0]
        .supporting_findings
    )

    assert len(findings) == 3

    assert all(
        not finding.startswith("E_")
        for finding in findings
    )

    assert any(
        "severe Chronic Obstructive Pulmonary Disease"
        in finding
        for finding in findings
    )

    assert any(
        "shortness of breath"
        in finding
        for finding in findings
    )

    assert any(
        "colored or more abundant sputum"
        in finding
        for finding in findings
    )


def test_observed_initial_evidence_cannot_be_missing():
    result = EvidenceSemanticNormalizer.normalize(
        _request(),
        _response(
            missing=[
                "E_77",
            ]
        ),
    )

    assert (
        result
        .candidate_reasoning[0]
        .missing_information
        == []
    )


def test_explicitly_answered_code_cannot_be_missing():
    result = EvidenceSemanticNormalizer.normalize(
        _request(),
        _response(
            missing=[
                "E_72",
            ]
        ),
    )

    assert (
        result
        .candidate_reasoning[0]
        .missing_information
        == []
    )


def test_no_information_is_missing_sentinel_becomes_empty():
    result = EvidenceSemanticNormalizer.normalize(
        _request(),
        _response(
            missing=[
                "No information is missing.",
            ]
        ),
    )

    assert (
        result
        .candidate_reasoning[0]
        .missing_information
        == []
    )


def test_non_evidence_text_is_preserved():
    result = EvidenceSemanticNormalizer.normalize(
        _request(),
        _response(
            supporting=[
                "Recent symptom progression",
            ],
            missing=[
                "Oxygen saturation",
            ],
        ),
    )

    candidate = result.candidate_reasoning[0]

    assert candidate.supporting_findings == [
        "Recent symptom progression"
    ]

    assert candidate.missing_information == [
        "Oxygen saturation"
    ]


def test_candidate_identity_is_never_changed():
    response = _response(
        supporting=["E_31"]
    )

    result = EvidenceSemanticNormalizer.normalize(
        _request(),
        response,
    )

    candidate = result.candidate_reasoning[0]

    assert candidate.rank == 1
    assert candidate.disease == "Bronchiectasis"
