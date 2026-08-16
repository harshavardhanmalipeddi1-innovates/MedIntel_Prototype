from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.reasoning_schema import ClinicalReasoningResponse
from backend.app.schemas.verification_schema import ClinicalVerificationResponse
from backend.app.schemas.treatment_schema import TreatmentDraftResponse
from uuid import uuid4


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClinicalWorkflowRequest(StrictSchema):
    """
    Complete clinical workflow input.

    The workflow starts from clinician-supplied patient data and
    executes the existing prediction, reasoning, verification,
    and treatment-safety stages.
    """

    patient_context: Dict[str, Any] = Field(default_factory=dict)


class ClinicalWorkflowResponse(StrictSchema):
    """
    Complete MedIntel clinical workflow result.

    The workflow provides clinical decision support only.
    Final diagnosis and treatment decisions remain with the doctor.
    """

    success: bool = True

    predictions: list = Field(default_factory=list)

    reasoning: Optional[ClinicalReasoningResponse] = None

    verification: Optional[ClinicalVerificationResponse] = None

    treatment_draft: Optional[TreatmentDraftResponse] = None

    workflow_status: str = Field(default="COMPLETED")
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))

    requires_doctor_review: bool = True

    doctor_approval_status: str = "PENDING"