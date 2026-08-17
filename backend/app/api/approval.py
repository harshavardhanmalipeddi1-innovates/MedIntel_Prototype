from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.auth import require_clinician
from backend.app.schemas.approval_schema import (
    DoctorApprovalRequest,
    DoctorApprovalResponse,
)
from backend.app.schemas.auth_schema import ClinicianIdentity
from backend.services.approval_service import ApprovalService


router = APIRouter(
    prefix="/approval",
    tags=["doctor approval"],
)


def get_approval_service() -> ApprovalService:
    return ApprovalService()


@router.post(
    "/{workflow_id}",
    response_model=DoctorApprovalResponse,
)
def review_workflow(
    workflow_id: str,
    request: DoctorApprovalRequest,
    clinician: Annotated[
        ClinicianIdentity,
        Depends(require_clinician),
    ],
    service: ApprovalService = Depends(get_approval_service),
) -> DoctorApprovalResponse:

    return service.approve_workflow(
        workflow_id=workflow_id,
        request=request,
        clinician_username=clinician.username,
    )


@router.get(
    "/{workflow_id}",
    response_model=DoctorApprovalResponse,
)
def get_workflow_approval(
    workflow_id: str,
    clinician: Annotated[
        ClinicianIdentity,
        Depends(require_clinician),
    ],
    service: ApprovalService = Depends(get_approval_service),
) -> DoctorApprovalResponse:

    return service.get_approval(workflow_id)