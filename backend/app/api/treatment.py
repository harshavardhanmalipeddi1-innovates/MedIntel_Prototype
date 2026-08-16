from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.schemas.reasoning_schema import ClinicalReasoningRequest, ClinicalReasoningResponse
from backend.app.schemas.treatment_schema import TreatmentDraftResponse
from backend.services.treatment_draft_service import TreatmentDraftService

router = APIRouter()

class TreatmentDraftRequest(BaseModel):
    reasoning_request: ClinicalReasoningRequest
    reasoning_response: ClinicalReasoningResponse

def get_treatment_service() -> TreatmentDraftService:
    return TreatmentDraftService()

@router.post("/treatment-draft", response_model=TreatmentDraftResponse)
def generate_treatment_draft(
    request: TreatmentDraftRequest,
    service: TreatmentDraftService = Depends(get_treatment_service)
):
    """
    Generates a safe treatment draft based on validated AI reasoning and the Knowledge Base.
    Explicitly enforces doctor review.
    """
    return service.generate_draft(
        request.reasoning_request,
        request.reasoning_response
    )
