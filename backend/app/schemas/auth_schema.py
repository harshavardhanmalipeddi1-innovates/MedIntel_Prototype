from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClinicianLoginRequest(StrictSchema):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8, max_length=256)


class ClinicianIdentity(StrictSchema):
    username: str
    role: Literal["clinician"] = "clinician"


class ClinicianTokenResponse(StrictSchema):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_seconds: int
    clinician: ClinicianIdentity
