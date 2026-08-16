import logging
import re

import pytest

from backend.app.schemas.workflow_schema import ClinicalWorkflowRequest
from backend.services.workflow_service import WorkflowService


@pytest.mark.asyncio
async def test_workflow_generates_correlation_id(caplog):
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

    messages = [
        record.getMessage()
        for record in caplog.records
    ]

    workflow_ids = []

    for message in messages:
        match = re.search(
            r"workflow_id=([a-f0-9-]+)",
            message,
        )

        if match:
            workflow_ids.append(match.group(1))

    assert workflow_ids
    assert len(set(workflow_ids)) == 1


@pytest.mark.asyncio
async def test_each_workflow_gets_unique_id():
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

    result1 = await service.run_workflow(request)
    result2 = await service.run_workflow(request)

    assert result1.workflow_id != result2.workflow_id


def test_workflow_id_is_not_patient_data():
    from backend.app.schemas.workflow_schema import (
        ClinicalWorkflowResponse,
    )

    response = ClinicalWorkflowResponse(
        success=True,
        predictions=[],
    )

    workflow_id = response.workflow_id

    assert workflow_id
    assert "patient" not in workflow_id.lower()
    assert "name" not in workflow_id.lower()
    assert "phone" not in workflow_id.lower()
    assert "mrn" not in workflow_id.lower()