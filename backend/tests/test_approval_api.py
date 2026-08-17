from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_approval_api_route_exists():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/clinical/approval/{workflow_id}" in paths

    approval_path = paths["/api/v1/clinical/approval/{workflow_id}"]

    assert "post" in approval_path
    assert "get" in approval_path


def test_approval_api_requires_authentication():
    response = client.post(
        "/api/v1/clinical/approval/workflow-api-001",
        json={
            "status": "APPROVED",
            "review_comment": "Reviewed by clinician.",
        },
    )

    assert response.status_code == 401


def test_approval_api_rejects_unknown_request_fields(
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/v1/clinical/approval/workflow-api-002",
        json={
            "status": "APPROVED",
            "review_comment": "Reviewed.",
            "reviewed_by": "attacker",
        },
    )

    assert response.status_code == 422
def test_approval_api_approves_workflow(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/clinical/approval/workflow-api-001",
        json={
            "status": "APPROVED",
            "review_comment": "Reviewed and approved by clinician.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["workflow_id"] == "workflow-api-001"
    assert data["requires_doctor_review"] is True
    assert data["approval_status"] == "APPROVED"
    assert data["reviewed_by"] == "test-clinician"
    assert data["review_comment"] == (
        "Reviewed and approved by clinician."
    )


def test_approval_api_rejects_workflow(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/clinical/approval/workflow-api-002",
        json={
            "status": "REJECTED",
            "review_comment": "Requires additional clinical review.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["workflow_id"] == "workflow-api-002"
    assert data["requires_doctor_review"] is True
    assert data["approval_status"] == "REJECTED"
    assert data["reviewed_by"] == "test-clinician"


def test_approval_api_prevents_double_review(authenticated_client):
    workflow_id = "workflow-api-double"

    first = authenticated_client.post(
        f"/api/v1/clinical/approval/{workflow_id}",
        json={
            "status": "APPROVED",
            "review_comment": "First review.",
        },
    )

    assert first.status_code == 200

    second = authenticated_client.post(
        f"/api/v1/clinical/approval/{workflow_id}",
        json={
            "status": "REJECTED",
            "review_comment": "Second review should fail.",
        },
    )

    assert second.status_code == 409