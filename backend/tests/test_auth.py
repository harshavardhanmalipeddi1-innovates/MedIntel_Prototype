import unittest

import bcrypt
from fastapi.testclient import TestClient

from backend.app.config.settings import settings
from backend.app.main import app


class ClinicianAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.original = (
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

        self.client = TestClient(app)

    def tearDown(self):
        (
            settings.JWT_SECRET,
            settings.CLINICIAN_USERNAME,
            settings.CLINICIAN_PASSWORD_HASH,
        ) = self.original

    def login(self):
        return self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "test-clinician",
                "password": "TestClinicianPassword123!",
            },
        )

    def test_valid_login_and_me(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["token_type"], "bearer")
        self.assertTrue(data["access_token"])
        self.assertEqual(
            data["clinician"]["username"],
            "test-clinician",
        )
        self.assertEqual(
            data["clinician"]["role"],
            "clinician",
        )

        me = self.client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization":
                    f"Bearer {data['access_token']}"
            },
        )

        self.assertEqual(me.status_code, 200)
        self.assertEqual(
            me.json()["username"],
            "test-clinician",
        )

    def test_wrong_password_is_unauthorized(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "test-clinician",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_malformed_token_is_unauthorized(self):
        response = self.client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization":
                    "Bearer not-a-valid-jwt"
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_clinical_route_requires_bearer_token(self):
        response = self.client.get(
            "/api/v1/clinical/assessment/questionnaire"
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
