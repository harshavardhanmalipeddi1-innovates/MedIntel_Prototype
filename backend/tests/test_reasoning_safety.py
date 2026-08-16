import pytest
from backend.app.modules.reasoning_engine.safety_validator import SafetyValidator
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ReasoningDifferentialItem,
    ClinicalRuleResult,
    ClinicalReasoningResponse,
    CandidateReasoning
)

@pytest.fixture
def sample_request():
    return ClinicalReasoningRequest(
        patient_context={"age": 45},
        rules=ClinicalRuleResult(),
        differential=[
            ReasoningDifferentialItem(rank=1, disease="Pneumonia", probability=0.85, confidence="High"),
            ReasoningDifferentialItem(rank=2, disease="Asthma", probability=0.15, confidence="Low")
        ]
    )

def test_safety_validator_valid(sample_request):
    response = ClinicalReasoningResponse(
        candidate_reasoning=[
            CandidateReasoning(rank=1, disease="Pneumonia", rationale="Safe"),
            CandidateReasoning(rank=2, disease="Asthma", rationale="Safe")
        ],
        reasoning_summary="Summary",
        requires_doctor_review=True
    )
    assert SafetyValidator.validate(sample_request, response)

def test_safety_validator_rank_changed(sample_request):
    response = ClinicalReasoningResponse(
        candidate_reasoning=[
            CandidateReasoning(rank=2, disease="Pneumonia", rationale="Safe"),
            CandidateReasoning(rank=1, disease="Asthma", rationale="Safe")
        ],
        reasoning_summary="Summary",
        requires_doctor_review=True
    )
    with pytest.raises(ValueError, match="Safety Violation: Candidate rank changed"):
        SafetyValidator.validate(sample_request, response)

def test_safety_validator_disease_changed(sample_request):
    response = ClinicalReasoningResponse(
        candidate_reasoning=[
            CandidateReasoning(rank=1, disease="COPD", rationale="Safe"),
            CandidateReasoning(rank=2, disease="Asthma", rationale="Safe")
        ],
        reasoning_summary="Summary",
        requires_doctor_review=True
    )
    with pytest.raises(ValueError, match="Safety Violation: Candidate disease changed"):
        SafetyValidator.validate(sample_request, response)

def test_safety_validator_candidate_added_or_removed(sample_request):
    response = ClinicalReasoningResponse(
        candidate_reasoning=[
            CandidateReasoning(rank=1, disease="Pneumonia", rationale="Safe")
        ],
        reasoning_summary="Summary",
        requires_doctor_review=True
    )
    with pytest.raises(ValueError, match="Safety Violation: Number of candidates was changed"):
        SafetyValidator.validate(sample_request, response)



@pytest.mark.parametrize(
    "unsafe_text",
    [
        "This is the most likely diagnosis.",
        "The diagnosis is Pneumonia.",
        "These findings confirm the diagnosis.",
        "The evidence supports this conclusion.",
    ],
)
def test_safety_validator_rejects_authoritative_diagnostic_wording(
    sample_request,
    unsafe_text,
):
    response = ClinicalReasoningResponse(
        candidate_reasoning=[
            CandidateReasoning(
                rank=1,
                disease="Pneumonia",
                rationale=unsafe_text,
            ),
            CandidateReasoning(
                rank=2,
                disease="Asthma",
                rationale="Requires clinician verification.",
            ),
        ],
        reasoning_summary="Further clinical verification is required.",
        requires_doctor_review=True,
    )

    with pytest.raises(
        ValueError,
        match="Authoritative diagnostic wording",
    ):
        SafetyValidator.validate(sample_request, response)


def test_safety_validator_allows_explicit_diagnostic_uncertainty(
    sample_request,
):
    response = ClinicalReasoningResponse(
        candidate_reasoning=[
            CandidateReasoning(
                rank=1,
                disease="Pneumonia",
                rationale=(
                    "Diagnosis is not confirmed. Findings support "
                    "consideration of this existing candidate."
                ),
            ),
            CandidateReasoning(
                rank=2,
                disease="Asthma",
                rationale="Requires clinician verification.",
            ),
        ],
        reasoning_summary="Further clinical verification is required.",
        requires_doctor_review=True,
    )

    assert SafetyValidator.validate(sample_request, response)
