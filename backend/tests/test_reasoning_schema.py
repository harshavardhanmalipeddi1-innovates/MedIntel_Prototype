import pytest
from pydantic import ValidationError

from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
)


def _candidate(rank: int = 1):
    return {
        "rank": rank,
        "disease": "Pneumonia",
        "probability": 0.82,
        "confidence": "medium",
        "knowledge": {
            "disease_id": "pneumonia",
            "name": "Pneumonia",
            "description": "Infection involving the lung parenchyma.",
            "knowledge_version": "1.0",
        },
    }


def _reasoning_response():
    return {
        "candidate_reasoning": [
            {
                "rank": 1,
                "disease": "Pneumonia",
                "supporting_findings": ["Cough"],
                "conflicting_findings": [],
                "missing_information": ["Oxygen saturation"],
                "rationale": (
                    "The supplied findings are compatible with this "
                    "existing differential candidate."
                ),
            }
        ],
        "important_uncertainties": [
            "Oxygen saturation has not been supplied."
        ],
        "red_flags_to_review": [],
        "next_information_needed": [
            "Review oxygen saturation."
        ],
        "reasoning_summary": (
            "Further clinical verification is required."
        ),
        "limitations": [
            "Reasoning is limited to the supplied clinical information."
        ],
        "requires_doctor_review": True,
    }


def test_reasoning_request_matches_existing_pipeline_shape():
    request = ClinicalReasoningRequest(
        patient_context={
            "cough": True,
            "breathlessness": True,
        },
        rules={
            "alerts": [
                "Check oxygen saturation and respiratory status"
            ],
            "status": "evaluated",
        },
        differential=[_candidate()],
    )

    assert request.differential[0].rank == 1
    assert request.differential[0].disease == "Pneumonia"
    assert request.differential[0].knowledge is not None


def test_reasoning_request_rejects_invalid_probability():
    candidate = _candidate()
    candidate["probability"] = 1.5

    with pytest.raises(ValidationError):
        ClinicalReasoningRequest(
            patient_context={},
            differential=[candidate],
        )


def test_reasoning_request_rejects_more_than_five_candidates():
    candidates = [_candidate(rank=i) for i in range(1, 7)]

    with pytest.raises(ValidationError):
        ClinicalReasoningRequest(
            patient_context={},
            differential=candidates,
        )


def test_reasoning_response_requires_doctor_review():
    response = _reasoning_response()
    response["requires_doctor_review"] = False

    with pytest.raises(ValidationError):
        ClinicalReasoningResponse(**response)


def test_reasoning_response_rejects_final_diagnosis():
    response = _reasoning_response()
    response["final_diagnosis"] = "Pneumonia"

    with pytest.raises(ValidationError):
        ClinicalReasoningResponse(**response)


def test_reasoning_response_rejects_prescription():
    response = _reasoning_response()
    response["prescription"] = "Example medication"

    with pytest.raises(ValidationError):
        ClinicalReasoningResponse(**response)


def test_valid_reasoning_response():
    response = ClinicalReasoningResponse(**_reasoning_response())

    assert response.requires_doctor_review is True
    assert response.candidate_reasoning[0].rank == 1
    assert response.candidate_reasoning[0].disease == "Pneumonia"
