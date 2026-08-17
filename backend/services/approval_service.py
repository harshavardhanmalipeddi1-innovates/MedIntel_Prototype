from datetime import datetime, timezone

from fastapi import HTTPException, status

from backend.app.schemas.approval_schema import (
    DoctorApprovalRequest,
    DoctorApprovalResponse,
)
from backend.services.firestore_service import FirestoreService


class ApprovalService:
    """
    Handles clinician approval/rejection of completed MedIntel workflows.

    Approval is an explicit clinician action.
    AI-generated workflow results remain pending until reviewed.
    """

    COLLECTION = "clinical_workflow_approvals"

    def __init__(self, firestore_service: FirestoreService | None = None):
        self.firestore = firestore_service or FirestoreService()

    def get_approval(
        self,
        workflow_id: str,
    ) -> DoctorApprovalResponse:
        document = self.firestore.get_document(
            self.COLLECTION,
            workflow_id,
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow approval record not found.",
            )

        return DoctorApprovalResponse(
            workflow_id=workflow_id,
            requires_doctor_review=True,
            approval_status=document.get(
                "approval_status",
                "PENDING",
            ),
            reviewed_by=document.get("reviewed_by"),
            reviewed_at=document.get("reviewed_at"),
            review_comment=document.get("review_comment"),
        )

    def approve_workflow(
        self,
        workflow_id: str,
        request: DoctorApprovalRequest,
        clinician_username: str,
    ) -> DoctorApprovalResponse:

        if request.status not in {"APPROVED", "REJECTED"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Approval status must be APPROVED or REJECTED.",
            )

        existing = self.firestore.get_document(
            self.COLLECTION,
            workflow_id,
        )

        # If an approval already exists, do not silently overwrite it.
        if existing is not None:
            existing_status = existing.get(
                "approval_status",
                "PENDING",
            )

            if existing_status in {"APPROVED", "REJECTED"}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Workflow has already been reviewed.",
                )

        reviewed_at = datetime.now(timezone.utc)

        data = {
            "workflow_id": workflow_id,
            "requires_doctor_review": True,
            "approval_status": request.status,
            "reviewed_by": clinician_username,
            "reviewed_at": reviewed_at,
            "review_comment": request.review_comment,
        }

        if existing is None:
            self.firestore.add_document(
                self.COLLECTION,
                data,
            )
        else:
            self.firestore.update_document(
                self.COLLECTION,
                workflow_id,
                data,
            )

        return DoctorApprovalResponse(
            workflow_id=workflow_id,
            requires_doctor_review=True,
            approval_status=request.status,
            reviewed_by=clinician_username,
            reviewed_at=reviewed_at,
            review_comment=request.review_comment,
        )