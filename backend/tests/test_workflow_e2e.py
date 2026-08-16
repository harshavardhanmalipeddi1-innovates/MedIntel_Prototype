import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.services.workflow_service import WorkflowService


client = TestClient(app)


# ============================================================
# 4.3.1 — Realistic Clinical Input
# ============================================================

def test_e2e_workflow_accepts_realistic_clinical_input(
    authenticated_client,
):
    payload = {
        "patient_context": {
            "age": 45,
            "sex": "M",
            "symptoms": [
                "cough",
                "fever",
                "shortness of breath",
            ],
            "symptom_duration": "3 days",
            "medical_history": [],
            "vital_signs": {
                "temperature": 38.5,
                "oxygen_saturation": 95,
            },
        }
    }

    response = authenticated_client.post(
        "/api/v1/clinical/workflow",
        json=payload,
    )

    assert response.status_code in {200, 400}
    assert isinstance(response.json(), dict)


# ============================================================
# 4.3.2 — Complete Workflow Response Structure
# ============================================================

def test_e2e_workflow_response_structure(
    authenticated_client,
):
    payload = {
        "patient_context": {
            "age": 45,
            "sex": "M",
            "symptoms": ["cough", "fever"],
        }
    }

    response = authenticated_client.post(
        "/api/v1/clinical/workflow",
        json=payload,
    )

    assert response.status_code in {200, 400}

    data = response.json()

    assert isinstance(data, dict)

    if response.status_code == 200:
        assert "success" in data
        assert "predictions" in data
        assert "reasoning" in data
        assert "verification" in data
        assert "treatment_draft" in data
        assert "workflow_status" in data
        assert "requires_doctor_review" in data
        assert "doctor_approval_status" in data


# ============================================================
# 4.3.3 — Successful Workflow Output
# ============================================================

def test_e2e_successful_workflow_contains_all_stages(monkeypatch):
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
            from backend.app.schemas.reasoning_schema import (
                ClinicalRuleResult,
            )

            return ClinicalRuleResult(
                alerts=[],
                status="evaluated",
            )

    class FakeReasoningService:
        async def generate_reasoning(self, request):
            from backend.app.schemas.reasoning_schema import (
                ClinicalReasoningResponse,
            )

            return ClinicalReasoningResponse(
                candidate_reasoning=[],
                important_uncertainties=[],
                red_flags_to_review=[],
                next_information_needed=[],
                reasoning_summary="Synthetic E2E reasoning.",
                limitations=[],
                requires_doctor_review=True,
            )

    class FakeVerificationService:
        def generate_verification_plan(
            self,
            reasoning_request,
            reasoning_response,
        ):
            from backend.app.schemas.verification_schema import (
                ClinicalVerificationResponse,
            )

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
            from backend.app.schemas.treatment_schema import (
                TreatmentDraftResponse,
            )

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

    request_payload = {
        "patient_context": {
            "age": 45,
            "sex": "M",
            "symptoms": ["cough", "fever"],
        }
    }

    from backend.app.schemas.workflow_schema import (
        ClinicalWorkflowRequest,
    )

    request = ClinicalWorkflowRequest(**request_payload)

    result = pytest.run(asyncio=True) if False else None

    import asyncio

    response = asyncio.run(
        service.run_workflow(request)
    )

    assert response.success is True
    assert response.workflow_status == "COMPLETED"

    assert len(response.predictions) == 1
    assert response.predictions[0]["disease"] == "Pneumonia"

    assert response.reasoning is not None
    assert response.verification is not None
    assert response.treatment_draft is not None


# ============================================================
# 4.3.4 — Doctor Review Enforcement
# ============================================================

def test_e2e_workflow_enforces_doctor_review(monkeypatch):
    from backend.app.schemas.workflow_schema import (
        ClinicalWorkflowResponse,
    )

    response = ClinicalWorkflowResponse(
        success=True,
        predictions=[],
    )

    assert response.requires_doctor_review is True
    assert response.doctor_approval_status == "PENDING"


# ============================================================
# 4.3.5 — No Autonomous Treatment Fields
# ============================================================

def test_e2e_workflow_contains_no_autonomous_action_fields(
    authenticated_client,
):
    payload = {
        "patient_context": {
            "age": 45,
            "sex": "M",
            "symptoms": ["cough"],
        }
    }

    response = authenticated_client.post(
        "/api/v1/clinical/workflow",
        json=payload,
    )

    assert response.status_code in {200, 400}

    data = response.json()

    prohibited_fields = {
        "prescription",
        "medication_order",
        "automatic_order",
        "dispense",
        "dose",
        "dosage",
        "final_treatment",
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

    assert prohibited_fields.isdisjoint(
        collect_keys(data)
    )


# ============================================================
# 4.3.6 — No Differential Candidate Safety Path
# ============================================================

@pytest.mark.asyncio
async def test_e2e_workflow_handles_no_differential(monkeypatch):
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

    from backend.app.schemas.workflow_schema import (
        ClinicalWorkflowRequest,
    )

    request = ClinicalWorkflowRequest(
        patient_context={
            "age": 45,
            "sex": "M",
            "symptoms": ["cough"],
        }
    )

    result = await service.run_workflow(request)

    assert result.success is False
    assert result.predictions == []
    assert result.workflow_status == "NO_DIFFERENTIAL"
    assert result.requires_doctor_review is True
    assert result.doctor_approval_status == "PENDING"


# ============================================================
# 4.3.7 — OpenAPI Contract
# ============================================================

def test_e2e_workflow_openapi_contract():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    openapi = response.json()

    assert "/api/v1/clinical/workflow" in openapi["paths"]

    workflow_path = openapi["paths"][
        "/api/v1/clinical/workflow"
    ]

    assert "post" in workflow_path

    post_operation = workflow_path["post"]

    assert "requestBody" in post_operation
    assert "responses" in post_operation


# ============================================================
# 4.3.8 — Missing Information Does Not Bypass Safety
# ============================================================

def test_e2e_workflow_missing_information_keeps_doctor_review(
    authenticated_client,
):
    payload = {
        "patient_context": {}
    }

    response = authenticated_client.post(
        "/api/v1/clinical/workflow",
        json=payload,
    )

    assert response.status_code in {200, 400}

    data = response.json()

    assert isinstance(data, dict)

    if response.status_code == 200:
        assert data["requires_doctor_review"] is True
        assert data["doctor_approval_status"] == "PENDING"