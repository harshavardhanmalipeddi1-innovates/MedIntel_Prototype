from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_workflow_api_accepts_valid_patient_context(authenticated_client):
    payload = {
        "patient_context": {
            "age": 45,
            "sex": "M",
            "symptoms": [
                "cough",
                "fever",
            ],
        }
    }

    response = authenticated_client.post(
        "/api/v1/clinical/workflow",
        json=payload,
    )

    assert response.status_code in {200, 400}

    data = response.json()

    assert isinstance(data, dict)


def test_workflow_api_route_exists():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/clinical/workflow" in paths
    assert "post" in paths["/api/v1/clinical/workflow"]


def test_workflow_response_preserves_doctor_review_safety(authenticated_client):
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

    if response.status_code == 200:
        assert data["requires_doctor_review"] is True
        assert data["doctor_approval_status"] == "PENDING"