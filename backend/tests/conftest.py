import bcrypt
import pytest
from fastapi.testclient import TestClient

from backend.app.config.settings import settings
from backend.app.main import app


@pytest.fixture
def authenticated_client():
    """Create an authenticated clinician client for protected API tests."""
    original = (
        settings.JWT_SECRET,
        settings.CLINICIAN_USERNAME,
        settings.CLINICIAN_PASSWORD_HASH,
    )

    settings.JWT_SECRET = (
        "phase84-test-signing-secret-"
        "0123456789abcdef0123456789abcdef"
    )
    settings.CLINICIAN_USERNAME = "test-clinician"
    settings.CLINICIAN_PASSWORD_HASH = (
        bcrypt.hashpw(
            b"TestClinicianPassword123!",
            bcrypt.gensalt(rounds=4),
        ).decode("utf-8")
    )

    client = TestClient(app)

    try:
        login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "test-clinician",
                "password": "TestClinicianPassword123!",
            },
        )

        assert login.status_code == 200

        client.headers.update(
            {
                "Authorization":
                    f"Bearer {login.json()['access_token']}",
            }
        )

        yield client

    finally:
        (
            settings.JWT_SECRET,
            settings.CLINICIAN_USERNAME,
            settings.CLINICIAN_PASSWORD_HASH,
        ) = original
