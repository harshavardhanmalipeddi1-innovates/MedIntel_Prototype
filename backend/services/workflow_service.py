import logging

from backend.app.ml.feature_builder import FeatureBuilder
from backend.app.schemas.reasoning_schema import ClinicalReasoningRequest
from backend.app.schemas.workflow_schema import (
    ClinicalWorkflowRequest,
    ClinicalWorkflowResponse,
)
from backend.services.approval_service import ApprovalService
from backend.services.clinical_rules import ClinicalRules
from backend.services.differential_manager import DifferentialDiagnosisManager
from backend.services.prediction_service import PredictionService
from backend.services.reasoning_service import ReasoningService
from backend.services.treatment_draft_service import TreatmentDraftService
from backend.services.verification_service import VerificationService


logger = logging.getLogger(__name__)


class WorkflowService:
    """
    Coordinates the complete MedIntel clinical decision-support workflow.

    Existing services remain responsible for their individual stages.
    This service only orchestrates them.

    Final diagnosis and treatment decisions remain with the doctor.
    """

    def __init__(self):
        self.feature_builder = FeatureBuilder()
        self.prediction_service = PredictionService()
        self.differential_manager = DifferentialDiagnosisManager()
        self.clinical_rules = ClinicalRules()
        self.reasoning_service = ReasoningService()
        self.approval_service = ApprovalService()
        self.verification_service = VerificationService()
        self.treatment_service = TreatmentDraftService()

    async def run_workflow(
        self,
        request: ClinicalWorkflowRequest,
    ) -> ClinicalWorkflowResponse:
        """
        Execute the complete clinical workflow.
        """

        from uuid import uuid4

        workflow_id = str(uuid4())

        logger.info(
            "MedIntel clinical workflow started workflow_id=%s",
            workflow_id,
        )

        patient_context = request.patient_context

        # ---------------------------------------------------------
        # 1. Feature Building
        # ---------------------------------------------------------
        features = self.feature_builder.build_feature_vector(
            patient_context
        )

        # ---------------------------------------------------------
        # 2. Primary Prediction
        # ---------------------------------------------------------
        prediction_result = (
            self.prediction_service.predict_primary_disease(
                features.toarray()
                if hasattr(features, "toarray")
                else features
            )
        )

        logger.info("Primary prediction completed")

        # ---------------------------------------------------------
        # 3. Differential Diagnosis
        # ---------------------------------------------------------
        raw_probabilities = {
            item["condition"]: item["probability"]
            for item in prediction_result.get("predictions", [])
        }

        differential_result = (
            self.differential_manager.generate_differential(
                raw_probabilities
            )
        )

        differential = differential_result.get("predictions", [])

        logger.info(
            "Differential diagnosis generated: %d candidate(s)",
            len(differential),
        )

        if not differential:
            logger.warning(
                "Workflow stopped because no differential candidates "
                "were generated."
            )

            return ClinicalWorkflowResponse(
                workflow_id=workflow_id,
                success=False,
                predictions=[],
                workflow_status="NO_DIFFERENTIAL",
                requires_doctor_review=True,
                doctor_approval_status="PENDING",
            )

        # ---------------------------------------------------------
        # 4. Clinical Safety Rules
        # ---------------------------------------------------------
        rules_result = self.clinical_rules.evaluate(
            patient_context
        )

        logger.info("Clinical rules evaluation completed")

        # ---------------------------------------------------------
        # 5. Build Reasoning Request
        # ---------------------------------------------------------
        reasoning_request = ClinicalReasoningRequest(
            patient_context=patient_context,
            rules=rules_result,
            differential=differential,
        )

        # ---------------------------------------------------------
        # 6. Clinical Reasoning
        # ---------------------------------------------------------
        reasoning_response = (
            await self.reasoning_service.generate_reasoning(
                reasoning_request
            )
        )

        logger.info("Clinical reasoning completed")

        # ---------------------------------------------------------
        # 7. Verification Plan
        # ---------------------------------------------------------
        verification_response = (
            self.verification_service.generate_verification_plan(
                reasoning_request,
                reasoning_response,
            )
        )

        logger.info("Clinical verification plan generated")

        # ---------------------------------------------------------
        # 8. Treatment Safety Draft
        # ---------------------------------------------------------
        treatment_response = self.treatment_service.generate_draft(
            reasoning_request,
            reasoning_response,
        )

        logger.info("Treatment safety draft generated")

        # ---------------------------------------------------------
        # 9. Persist Doctor Approval State
        # ---------------------------------------------------------
        self.approval_service.create_pending_approval(
            workflow_id=workflow_id,
        )

        logger.info(
            "Doctor approval record created workflow_id=%s",
            workflow_id,
        )

        # ---------------------------------------------------------
        # 10. Final Workflow Response
        # ---------------------------------------------------------
        logger.info("MedIntel clinical workflow completed")

        return ClinicalWorkflowResponse(
            workflow_id=workflow_id,
            success=True,
            predictions=differential,
            reasoning=reasoning_response,
            verification=verification_response,
            treatment_draft=treatment_response,
            workflow_status="COMPLETED",
            requires_doctor_review=True,
            doctor_approval_status="PENDING",
        )