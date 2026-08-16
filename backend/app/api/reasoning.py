from fastapi import APIRouter, HTTPException, Depends
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse
)
from backend.services.reasoning_service import ReasoningService

router = APIRouter()

def get_reasoning_service() -> ReasoningService:
    return ReasoningService()

@router.post("/reasoning", response_model=ClinicalReasoningResponse)
async def generate_reasoning(
    request: ClinicalReasoningRequest,
    service: ReasoningService = Depends(get_reasoning_service)
):
    """
    Generates clinical reasoning for a given patient context and differential diagnosis.
    The response strictly adheres to MedIntel safety guidelines.
    """
    try:
        response = await service.generate_reasoning(request)
        return response
    except Exception as e:
        # We only catch top-level exceptions that escaped the service's own degraded fallbacks
        raise HTTPException(status_code=500, detail="An internal error occurred in the reasoning service.")
