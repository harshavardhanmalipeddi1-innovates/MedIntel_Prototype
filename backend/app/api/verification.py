from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.schemas.reasoning_schema import ClinicalReasoningRequest, ClinicalReasoningResponse
from backend.app.schemas.verification_schema import ClinicalVerificationResponse
from backend.services.verification_service import VerificationService

router = APIRouter()

class VerificationRequest(BaseModel):
    reasoning_request: ClinicalReasoningRequest
    reasoning_response: ClinicalReasoningResponse

def get_verification_service() -> VerificationService:
    return VerificationService()

@router.post("/verification", response_model=ClinicalVerificationResponse)
def generate_verification(
    request: VerificationRequest,
    service: VerificationService = Depends(get_verification_service)
):
    """
    Suggests clinical verification steps based on the reasoning and Knowledge Base.
    """
    return service.generate_verification_plan(
        request.reasoning_request,
        request.reasoning_response
    )
