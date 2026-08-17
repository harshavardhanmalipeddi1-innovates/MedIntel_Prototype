import pytest

from backend.app.schemas.approval_schema import (
    DoctorApprovalRequest,
    DoctorApprovalResponse,
)
from backend.services.approval_service import ApprovalService


class FakeFirestoreService:
    def __init__(self):
        self.documents = {}

    def get_document(self, collection, doc_id):
        return self.documents.get((collection, doc_id))
    
    def set_document(self, collection, doc_id, data):
        self.documents[(collection, doc_id)] = data
    def add_document(self, collection, data):
        doc_id = data["workflow_id"]
        self.documents[(collection, doc_id)] = data
        return doc_id
    def update_document(self, collection, doc_id, data):
        if (collection, doc_id) not in self.documents:
            raise KeyError(doc_id)

        self.documents[(collection, doc_id)].update(data)


def test_approval_service_approves_workflow():
    firestore = FakeFirestoreService()
    service = ApprovalService(firestore)

    request = DoctorApprovalRequest(
        status="APPROVED",
        review_comment="Reviewed by clinician.",
    )

    response = service.approve_workflow(
        workflow_id="workflow-123",
        request=request,
        clinician_username="doctor1",
    )

    assert isinstance(response, DoctorApprovalResponse)
    assert response.workflow_id == "workflow-123"
    assert response.requires_doctor_review is True
    assert response.approval_status == "APPROVED"
    assert response.reviewed_by == "doctor1"
    assert response.reviewed_at is not None
    assert response.review_comment == "Reviewed by clinician."


def test_approval_service_rejects_workflow():
    firestore = FakeFirestoreService()
    service = ApprovalService(firestore)

    request = DoctorApprovalRequest(
        status="REJECTED",
        review_comment="Additional clinical review required.",
    )

    response = service.approve_workflow(
        workflow_id="workflow-456",
        request=request,
        clinician_username="doctor1",
    )

    assert response.approval_status == "REJECTED"
    assert response.requires_doctor_review is True
    assert response.reviewed_by == "doctor1"


def test_approval_is_persisted():
    firestore = FakeFirestoreService()
    service = ApprovalService(firestore)

    request = DoctorApprovalRequest(
        status="APPROVED",
        review_comment="Approved after review.",
    )

    service.approve_workflow(
        workflow_id="workflow-789",
        request=request,
        clinician_username="doctor1",
    )

    stored = firestore.get_document(
        "clinical_workflow_approvals",
        "workflow-789",
    )

    assert stored is not None
    assert stored["workflow_id"] == "workflow-789"
    assert stored["approval_status"] == "APPROVED"
    assert stored["requires_doctor_review"] is True
    assert stored["reviewed_by"] == "doctor1"
    assert stored["reviewed_at"] is not None


def test_approval_status_can_be_retrieved():
    firestore = FakeFirestoreService()
    service = ApprovalService(firestore)

    request = DoctorApprovalRequest(
        status="APPROVED",
        review_comment="Reviewed.",
    )

    service.approve_workflow(
        workflow_id="workflow-999",
        request=request,
        clinician_username="doctor1",
    )

    response = service.get_approval("workflow-999")

    assert response.workflow_id == "workflow-999"
    assert response.approval_status == "APPROVED"
    assert response.requires_doctor_review is True
    assert response.reviewed_by == "doctor1"


def test_double_review_is_rejected():
    firestore = FakeFirestoreService()
    service = ApprovalService(firestore)

    first_request = DoctorApprovalRequest(
        status="APPROVED",
        review_comment="First review.",
    )

    service.approve_workflow(
        workflow_id="workflow-double",
        request=first_request,
        clinician_username="doctor1",
    )

    second_request = DoctorApprovalRequest(
        status="REJECTED",
        review_comment="Second review.",
    )

    with pytest.raises(Exception) as exc_info:
        service.approve_workflow(
            workflow_id="workflow-double",
            request=second_request,
            clinician_username="doctor2",
        )

    assert exc_info.value.status_code == 409


def test_unknown_approval_fields_are_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DoctorApprovalRequest(
            status="APPROVED",
            review_comment="Valid comment.",
            reviewed_by="attacker",
        )


def test_approval_request_only_allows_approved_or_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DoctorApprovalRequest(
            status="PENDING",
        )


def test_reviewed_by_cannot_be_supplied_by_request():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DoctorApprovalRequest(
            status="APPROVED",
            reviewed_by="fake-doctor",
        )


def test_approval_response_requires_doctor_review():
    response = DoctorApprovalResponse(
        workflow_id="workflow-safety",
        approval_status="APPROVED",
        reviewed_by="doctor1",
    )

    assert response.requires_doctor_review is True


def test_missing_approval_record_returns_not_found():
    from fastapi import HTTPException

    firestore = FakeFirestoreService()
    service = ApprovalService(firestore)

    with pytest.raises(HTTPException) as exc_info:
        service.get_approval("does-not-exist")

    assert exc_info.value.status_code == 404