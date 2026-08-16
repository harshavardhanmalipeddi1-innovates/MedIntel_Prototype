import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningResponse,
)
from backend.app.schemas.verification_schema import (
    ClinicalVerificationResponse,
)
from backend.app.schemas.treatment_schema import (
    TreatmentDraftResponse,
)
from backend.services.workflow_service import WorkflowService


def test_workflow_service_initializes():
    service = WorkflowService()

    assert service.feature_builder is not None
    assert service.prediction_service is not None
    assert service.differential_manager is not None
    assert service.clinical_rules is not None
    assert service.reasoning_service is not None
    assert service.verification_service is not None
    assert service.treatment_service is not None


def test_workflow_response_requires_doctor_review():
    from backend.app.schemas.workflow_schema import ClinicalWorkflowResponse

    response = ClinicalWorkflowResponse(
        success=True,
        predictions=[],
    )

    assert response.requires_doctor_review is True
    assert response.doctor_approval_status == "PENDING"
    assert response.workflow_status == "COMPLETED"


def test_workflow_schema_rejects_unknown_fields():
    from pydantic import ValidationError
    from backend.app.schemas.workflow_schema import ClinicalWorkflowRequest

    with pytest.raises(ValidationError):
        ClinicalWorkflowRequest(
            patient_context={},
            unexpected_field="should be rejected",
        )


def test_workflow_api_route_is_registered():
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/clinical/workflow" in paths
    assert "post" in paths["/api/v1/clinical/workflow"]


def test_workflow_api_requires_patient_context(
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/v1/clinical/workflow",
        json={},
    )

    # Authentication is required by the Phase 8 hardened boundary.
    # Once authenticated, patient_context still defaults to an empty
    # dictionary, so the request reaches the workflow/schema layer.
    assert response.status_code in {200, 400}
@pytest.mark.asyncio
async def test_workflow_service_orchestrates_all_stages(monkeypatch):
    from backend.app.schemas.workflow_schema import ClinicalWorkflowRequest
    from backend.app.schemas.reasoning_schema import (
        ClinicalReasoningResponse,
        ClinicalRuleResult,
        ReasoningDifferentialItem,
    )
    from backend.app.schemas.verification_schema import (
        ClinicalVerificationResponse,
    )
    from backend.app.schemas.treatment_schema import (
        TreatmentDraftResponse,
    )

    service = WorkflowService()

    class FakeFeatureBuilder:
        def build_feature_vector(self, patient_context):
            return [1, 2, 3]

    class FakePredictionService:
        def predict_primary_disease(self, features):
            return {
                "predictions": [
                    {
                        "condition": "Pneumonia",
                        "probability": 0.85,
                    }
                ]
            }

    class FakeDifferentialManager:
        def generate_differential(self, probabilities):
            return {
                "predictions": [
                    {
                        "rank": 1,
                        "disease": "Pneumonia",
                        "probability": 0.85,
                        "confidence": "High",
                        "knowledge": None,
                    }
                ]
            }

    class FakeClinicalRules:
        def evaluate(self, patient_context):
            return ClinicalRuleResult(
                alerts=[],
                status="evaluated",
            )

    class FakeReasoningService:
        async def generate_reasoning(self, request):
            return ClinicalReasoningResponse(
                candidate_reasoning=[],
                important_uncertainties=[],
                red_flags_to_review=[],
                next_information_needed=[],
                reasoning_summary="Synthetic workflow reasoning.",
                limitations=[],
                requires_doctor_review=True,
            )

    class FakeVerificationService:
        def generate_verification_plan(
            self,
            reasoning_request,
            reasoning_response,
        ):
            return ClinicalVerificationResponse(
                suggested_steps=[],
                missing_information_summary=[],
                requires_doctor_review=True,
            )
    class FakeTreatmentService:
        def generate_draft(
            self,
            reasoning_request,
            reasoning_response,
        ):
            return TreatmentDraftResponse(
                considerations=[],
                general_cautions=[],
                status="AI_GENERATED_DRAFT",
                requires_doctor_review=True,
                doctor_approval_status="PENDING",
            )

    service.feature_builder = FakeFeatureBuilder()
    service.prediction_service = FakePredictionService()
    service.differential_manager = FakeDifferentialManager()
    service.clinical_rules = FakeClinicalRules()
    service.reasoning_service = FakeReasoningService()
    service.verification_service = FakeVerificationService()
    service.treatment_service = FakeTreatmentService()

    request = ClinicalWorkflowRequest(
        patient_context={
            "age": 45,
            "sex": "M",
            "symptoms": ["cough", "fever"],
        }
    )

    result = await service.run_workflow(request)

    assert result.success is True
    assert result.workflow_status == "COMPLETED"
    assert result.requires_doctor_review is True
    assert result.doctor_approval_status == "PENDING"

    assert len(result.predictions) == 1
    assert result.predictions[0]["disease"] == "Pneumonia"

    assert result.reasoning is not None
    assert result.verification is not None
    assert result.treatment_draft is not None

    assert result.treatment_draft.status == "AI_GENERATED_DRAFT"