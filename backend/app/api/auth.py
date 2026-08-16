from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.auth import (
    authenticate_clinician,
    create_access_token,
    require_clinician,
)
from backend.app.schemas.auth_schema import (
    ClinicianIdentity,
    ClinicianLoginRequest,
    ClinicianTokenResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/login",
    response_model=ClinicianTokenResponse,
)
def login(
    request: ClinicianLoginRequest,
) -> ClinicianTokenResponse:
    clinician = authenticate_clinician(
        request.username,
        request.password,
    )

    token, expires_in_seconds = create_access_token(
        clinician
    )

    return ClinicianTokenResponse(
        access_token=token,
        expires_in_seconds=expires_in_seconds,
        clinician=clinician,
    )


@router.get(
    "/me",
    response_model=ClinicianIdentity,
)
def current_clinician(
    clinician: Annotated[
        ClinicianIdentity,
        Depends(require_clinician),
    ],
) -> ClinicianIdentity:
    return clinician
