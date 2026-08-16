from datetime import datetime, timedelta, timezone
from typing import Annotated
import secrets

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError, jwt

from backend.app.config.settings import settings
from backend.app.schemas.auth_schema import ClinicianIdentity


bearer_scheme = HTTPBearer(auto_error=False)


def _auth_not_configured() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Clinician authentication is not configured.",
    )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing clinician credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _ensure_auth_configured() -> None:
    required = (
        settings.JWT_SECRET,
        settings.CLINICIAN_USERNAME,
        settings.CLINICIAN_PASSWORD_HASH,
    )

    if not all(
        isinstance(value, str) and value.strip()
        for value in required
    ):
        raise _auth_not_configured()


def authenticate_clinician(
    username: str,
    password: str,
) -> ClinicianIdentity:
    _ensure_auth_configured()

    username_matches = secrets.compare_digest(
        username,
        settings.CLINICIAN_USERNAME,
    )

    try:
        password_matches = bcrypt.checkpw(
            password.encode("utf-8"),
            settings.CLINICIAN_PASSWORD_HASH.encode("utf-8"),
        )
    except (TypeError, ValueError):
        raise _auth_not_configured()

    # Evaluate both checks before rejecting to reduce account-enumeration
    # information leakage.
    if not (username_matches and password_matches):
        raise _unauthorized()

    return ClinicianIdentity(
        username=settings.CLINICIAN_USERNAME,
    )


def create_access_token(
    clinician: ClinicianIdentity,
) -> tuple[str, int]:
    _ensure_auth_configured()

    now = datetime.now(timezone.utc)

    expires_delta = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    expires_at = now + expires_delta

    payload = {
        "sub": clinician.username,
        "role": "clinician",
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.ALGORITHM,
    )

    return (
        token,
        int(expires_delta.total_seconds()),
    )


def require_clinician(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> ClinicianIdentity:
    _ensure_auth_configured()

    if credentials is None:
        raise _unauthorized()

    if credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise _unauthorized()

    subject = payload.get("sub")
    role = payload.get("role")
    token_type = payload.get("type")

    if not isinstance(subject, str):
        raise _unauthorized()

    if not secrets.compare_digest(
        subject,
        settings.CLINICIAN_USERNAME,
    ):
        raise _unauthorized()

    if role != "clinician":
        raise _unauthorized()

    if token_type != "access":
        raise _unauthorized()

    return ClinicianIdentity(
        username=subject,
    )
