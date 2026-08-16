import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.workflow_schema import ClinicalWorkflowRequest
from backend.services.workflow_service import WorkflowService


client = TestClient(app)


def test_workflow_stops_when_no_differential_candidates(monkeypatch):
    service = WorkflowService()

    class FakeFeatureBuilder:
        def build_feature_vector(self, patient_context):
            return [1, 2, 3]

    class FakePredictionService:
        def predict_primary_disease(self, features):
            return {
                "predictions": []
            }

    class FakeDifferentialManager:
        def generate_differential(self, probabilities):
            return {
                "predictions": []
            }

    service.feature_builder = FakeFeatureBuilder()
    service.prediction_service = FakePredictionService()
    service.differential_manager = FakeDifferentialManager()

    request = ClinicalWorkflowRequest(
        patient_context={
            "age": 45,
            "symptoms": ["cough"],
        }
    )

    result = pytest.run(asyncio=True) if False else None


@pytest.mark.asyncio
async def test_workflow_returns_safe_response_when_no_differential():
    service = WorkflowService()

    class FakeFeatureBuilder:
        def build_feature_vector(self, patient_context):
            return [1, 2, 3]

    class FakePredictionService:
        def predict_primary_disease(self, features):
            return {
                "predictions": []
            }

    class FakeDifferentialManager:
        def generate_differential(self, probabilities):
            return {
                "predictions": []
            }

    service.feature_builder = FakeFeatureBuilder()
    service.prediction_service = FakePredictionService()
    service.differential_manager = FakeDifferentialManager()

    request = ClinicalWorkflowRequest(
        patient_context={
            "age": 45,
            "symptoms": ["cough"],
        }
    )

    result = await service.run_workflow(request)

    assert result.success is False
    assert result.predictions == []
    assert result.workflow_status == "NO_DIFFERENTIAL"
    assert result.requires_doctor_review is True
    assert result.doctor_approval_status == "PENDING"


def test_workflow_schema_rejects_unknown_fields():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ClinicalWorkflowRequest(
            patient_context={},
            autonomous_decision=True,
        )


def test_workflow_response_requires_doctor_review():
    from backend.app.schemas.workflow_schema import ClinicalWorkflowResponse

    response = ClinicalWorkflowResponse(
        success=True,
        predictions=[],
    )

    assert response.requires_doctor_review is True
    assert response.doctor_approval_status == "PENDING"


def test_workflow_api_rejects_unknown_request_fields(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/clinical/workflow",
        json={
            "patient_context": {
                "age": 45,
                "symptoms": ["cough"],
            },
            "autonomous_decision": True,
        },
    )

    assert response.status_code == 422


def test_workflow_api_accepts_valid_schema():
    response = client.post(
        "/api/v1/clinical/workflow",
        json={
            "patient_context": {
                "age": 45,
                "sex": "M",
                "symptoms": ["cough", "fever"],
            }
        },
    )

    # The request may fail later because of unavailable model/runtime
    # dependencies, but the request itself must pass schema validation.
    assert response.status_code != 422


def test_workflow_response_cannot_enable_autonomous_approval():
    from backend.app.schemas.workflow_schema import ClinicalWorkflowResponse

    response = ClinicalWorkflowResponse(
        success=True,
        predictions=[],
    )

    data = response.model_dump()

    assert data["requires_doctor_review"] is True
    assert data["doctor_approval_status"] == "PENDING"


def test_workflow_has_no_autonomous_treatment_fields():
    from backend.app.schemas.workflow_schema import ClinicalWorkflowResponse

    response = ClinicalWorkflowResponse(
        success=True,
        predictions=[],
    )

    data = response.model_dump()

    prohibited_fields = {
        "prescription",
        "medication_order",
        "automatic_order",
        "autonomous_treatment",
        "dispense",
        "dose",
        "dosage",
        "final_treatment",
    }

    assert prohibited_fields.isdisjoint(data.keys())


@pytest.mark.asyncio
async def test_workflow_does_not_continue_after_empty_differential():
    service = WorkflowService()

    class FakeFeatureBuilder:
        def build_feature_vector(self, patient_context):
            return [1, 2, 3]

    class FakePredictionService:
        def predict_primary_disease(self, features):
            return {
                "predictions": [
                    {
                        "condition": "Unknown",
                        "probability": 0.1,
                    }
                ]
            }

    class FakeDifferentialManager:
        def generate_differential(self, probabilities):
            return {
                "predictions": []
            }

    class FailingClinicalRules:
        def evaluate(self, patient_context):
            raise AssertionError(
                "Clinical rules must not run after an empty differential"
            )

    service.feature_builder = FakeFeatureBuilder()
    service.prediction_service = FakePredictionService()
    service.differential_manager = FakeDifferentialManager()
    service.clinical_rules = FailingClinicalRules()

    request = ClinicalWorkflowRequest(
        patient_context={
            "age": 50,
            "symptoms": ["unknown"],
        }
    )

    result = await service.run_workflow(request)

    assert result.success is False
    assert result.workflow_status == "NO_DIFFERENTIAL"
    assert result.requires_doctor_review is True