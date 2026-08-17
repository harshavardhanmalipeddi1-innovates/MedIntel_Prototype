from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DoctorApprovalRequest(StrictSchema):
    """
    Request submitted by an authenticated clinician to review
    a completed MedIntel clinical workflow.
    """

    status: Literal["APPROVED", "REJECTED"]

    review_comment: str | None = Field(
        default=None,
        max_length=2000,
    )


class DoctorApprovalResponse(StrictSchema):
    """
    Persisted doctor-review state for a clinical workflow.
    """

    workflow_id: str

    requires_doctor_review: Literal[True] = True

    approval_status: Literal[
        "PENDING",
        "APPROVED",
        "REJECTED",
    ] = "PENDING"

    reviewed_by: str | None = None

    reviewed_at: datetime | None = None

    review_comment: str | None = None