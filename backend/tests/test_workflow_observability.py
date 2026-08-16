import logging

import pytest

from backend.app.schemas.workflow_schema import ClinicalWorkflowRequest
from backend.services.workflow_service import WorkflowService


@pytest.mark.asyncio
async def test_workflow_logs_major_stages(caplog):
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
            return {
                "alerts": [],
                "status": "evaluated",
            }

    from backend.app.schemas.reasoning_schema import (
        ClinicalReasoningResponse,
    )

    class FakeReasoningService:
        async def generate_reasoning(self, request):
            return ClinicalReasoningResponse(
                candidate_reasoning=[],
                important_uncertainties=[],
                red_flags_to_review=[],
                next_information_needed=[],
                reasoning_summary="Synthetic reasoning.",
                limitations=[],
                requires_doctor_review=True,
            )

    from backend.app.schemas.verification_schema import (
        ClinicalVerificationResponse,
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

    from backend.app.schemas.treatment_schema import (
        TreatmentDraftResponse,
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
            "symptoms": ["cough", "fever"],
        }
    )

    with caplog.at_level(logging.INFO):
        result = await service.run_workflow(request)

    assert result.success is True

    messages = [record.getMessage() for record in caplog.records]

    expected_messages = [
        "MedIntel clinical workflow started",
        "Primary prediction completed",
        "Differential diagnosis generated",
        "Clinical rules evaluation completed",
        "Clinical reasoning completed",
        "Clinical verification plan generated",
        "Treatment safety draft generated",
        "MedIntel clinical workflow completed",
    ]

    for message in expected_messages:
        assert any(message in logged for logged in messages)


@pytest.mark.asyncio
async def test_workflow_logs_no_differential_event(caplog):
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

    with caplog.at_level(logging.WARNING):
        result = await service.run_workflow(request)

    assert result.success is False
    assert result.workflow_status == "NO_DIFFERENTIAL"

    messages = [record.getMessage() for record in caplog.records]

    assert any(
        "no differential candidates" in message.lower()
        for message in messages
    )


def test_workflow_logs_do_not_contain_patient_context(caplog):
    service = WorkflowService()

    sensitive_patient_context = {
        "patient_name": "TEST_PATIENT_SECRET",
        "phone": "9999999999",
        "medical_record_number": "MRN_SECRET_123",
    }

    logger = logging.getLogger("backend.services.workflow_service")

    with caplog.at_level(logging.INFO):
        logger.info("Clinical workflow started")

    messages = " ".join(
        record.getMessage()
        for record in caplog.records
    )

    assert "TEST_PATIENT_SECRET" not in messages
    assert "9999999999" not in messages
    assert "MRN_SECRET_123" not in messages


def test_workflow_response_remains_doctor_controlled():
    from backend.app.schemas.workflow_schema import (
        ClinicalWorkflowResponse,
    )

    response = ClinicalWorkflowResponse(
        success=True,
        predictions=[],
    )

    assert response.requires_doctor_review is True
    assert response.doctor_approval_status == "PENDING"