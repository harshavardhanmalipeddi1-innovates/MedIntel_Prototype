import pytest
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
    ReasoningDifferentialItem,
    ClinicalRuleResult
)
from backend.app.schemas.knowledge_schema import DiseaseKnowledge
from backend.services.treatment_draft_service import TreatmentDraftService

def test_treatment_draft_service():
    req = ClinicalReasoningRequest(
        patient_context={},
        rules=ClinicalRuleResult(),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Pneumonia",
                probability=0.8,
                confidence="High",
                knowledge=DiseaseKnowledge(
                    disease_id="pneumonia",
                    name="Pneumonia",
                    description="Test knowledge record for pneumonia.",
                    knowledge_version="test-v1",
                    red_flags=[],
                    recommended_investigations=[],
                    common_symptoms=[],
                    associated_symptoms=[],
                    physical_examination=[],
                    differential_diagnoses=[],
                    contraindications=["Allergy to penicillin"]
                )
            )
        ]
    )
    res = ClinicalReasoningResponse(
        candidate_reasoning=[],
        reasoning_summary="Test clinical reasoning summary.",
        requires_doctor_review=True,
        red_flags_to_review=[]
    )
    
    service = TreatmentDraftService()
    draft = service.generate_draft(req, res)
    
    assert len(draft.considerations) == 1
    assert draft.status == "AI_GENERATED_DRAFT"
    assert draft.requires_doctor_review is True
    assert draft.doctor_approval_status == "PENDING"
    
    # Check for pneumonia high risk
    assert draft.considerations[0].contraindication_concern is True
    assert "Allergy to penicillin" in draft.considerations[0].warnings[-1]




def test_treatment_draft_handles_missing_knowledge():
    req = ClinicalReasoningRequest(
        patient_context={},
        rules=ClinicalRuleResult(),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Pneumonia",
                probability=0.8,
                confidence="High",
                knowledge=None,
            )
        ],
    )

    reasoning = ClinicalReasoningResponse(
        candidate_reasoning=[],
        reasoning_summary="Synthetic treatment safety test.",
        requires_doctor_review=True,
    )

    draft = TreatmentDraftService().generate_draft(req, reasoning)

    assert len(draft.considerations) == 1
    assert draft.considerations[0].contraindication_concern is False
    assert (
        "No structured disease knowledge is available"
        in draft.considerations[0].warnings[0]
    )
    assert draft.requires_doctor_review is True


def test_treatment_draft_propagates_missing_information():
    from backend.app.schemas.reasoning_schema import CandidateReasoning

    req = ClinicalReasoningRequest(
        patient_context={},
        rules=ClinicalRuleResult(),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Pneumonia",
                probability=0.8,
                confidence="High",
                knowledge=None,
            )
        ],
    )

    reasoning = ClinicalReasoningResponse(
        candidate_reasoning=[
            CandidateReasoning(
                rank=1,
                disease="Pneumonia",
                supporting_findings=[],
                conflicting_findings=[],
                missing_information=["oxygen saturation", "CBC"],
                rationale="Synthetic rationale.",
            )
        ],
        important_uncertainties=["CBC", "symptom duration"],
        next_information_needed=["chest imaging"],
        reasoning_summary="Synthetic treatment safety test.",
        requires_doctor_review=True,
    )

    draft = TreatmentDraftService().generate_draft(req, reasoning)

    assert draft.considerations[0].missing_information == sorted(
        {
            "oxygen saturation",
            "CBC",
            "symptom duration",
            "chest imaging",
        }
    )


def test_treatment_draft_contains_no_autonomous_action_fields():
    req = ClinicalReasoningRequest(
        patient_context={},
        rules=ClinicalRuleResult(),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Pneumonia",
                probability=0.8,
                confidence="High",
                knowledge=None,
            )
        ],
    )

    reasoning = ClinicalReasoningResponse(
        candidate_reasoning=[],
        reasoning_summary="Synthetic treatment safety test.",
        requires_doctor_review=True,
    )

    draft = TreatmentDraftService().generate_draft(req, reasoning)
    data = draft.model_dump()

    prohibited_fields = {
        "prescription",
        "medication_order",
        "dose",
        "dosage",
        "dispense",
        "final_treatment",
        "automatic_order",
    }

    def collect_keys(value):
        keys = set()

        if isinstance(value, dict):
            for key, child in value.items():
                keys.add(key)
                keys.update(collect_keys(child))

        elif isinstance(value, list):
            for child in value:
                keys.update(collect_keys(child))

        return keys

    assert prohibited_fields.isdisjoint(collect_keys(data))
    assert data["status"] == "AI_GENERATED_DRAFT"
    assert data["doctor_approval_status"] == "PENDING"
    assert data["requires_doctor_review"] is True


def test_treatment_schema_rejects_prescription_field():
    from pydantic import ValidationError
    from backend.app.schemas.treatment_schema import TreatmentDraftResponse

    with pytest.raises(ValidationError):
        TreatmentDraftResponse(
            considerations=[],
            general_cautions=[],
            prescription="Unsafe autonomous prescription",
        )


def test_treatment_draft_api(authenticated_client):
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)

    payload = {
        "reasoning_request": {
            "patient_context": {},
            "rules": {
                "alerts": [],
                "status": "evaluated",
            },
            "differential": [
                {
                    "rank": 1,
                    "disease": "Pneumonia",
                    "probability": 0.8,
                    "confidence": "High",
                    "knowledge": None,
                }
            ],
        },
        "reasoning_response": {
            "candidate_reasoning": [],
            "important_uncertainties": [],
            "red_flags_to_review": [],
            "next_information_needed": [],
            "reasoning_summary": "Synthetic treatment API test.",
            "limitations": [],
            "requires_doctor_review": True,
        },
    }

    response = authenticated_client.post(
        "/api/v1/clinical/treatment-draft",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "AI_GENERATED_DRAFT"
    assert data["doctor_approval_status"] == "PENDING"
    assert data["requires_doctor_review"] is True
    assert len(data["considerations"]) == 1
def test_treatment_kb_red_flag_is_screening_warning_only():
    request = ClinicalReasoningRequest(
        patient_context={},
        rules=ClinicalRuleResult(),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Bronchiectasis",
                probability=0.4,
                confidence="Low",
                knowledge=DiseaseKnowledge(
                    disease_id="bronchiectasis",
                    name="Bronchiectasis",
                    description="Synthetic KB record.",
                    knowledge_version="test-v1",
                    red_flags=["Marked hypoxemia"],
                ),
            )
        ],
    )

    reasoning = ClinicalReasoningResponse(
        candidate_reasoning=[],
        reasoning_summary="Synthetic reasoning.",
        requires_doctor_review=True,
    )

    draft = TreatmentDraftService().generate_draft(
        request,
        reasoning,
    )

    warning = next(
        item
        for item in draft.considerations[0].warnings
        if "red-flag screening item" in item
    )

    assert "check for: Marked hypoxemia" in warning

    assert (
        "does not establish that the finding is present"
        in warning
    )

    assert "PRESENT" not in warning
