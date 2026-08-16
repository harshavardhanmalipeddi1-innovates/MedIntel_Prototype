from fastapi import APIRouter, HTTPException
import logging

from backend.app.schemas.workflow_schema import (
    ClinicalWorkflowRequest,
    ClinicalWorkflowResponse,
)
from backend.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

router = APIRouter()

workflow_service = WorkflowService()


@router.post(
    "/workflow",
    response_model=ClinicalWorkflowResponse,
)
async def run_workflow(
    request: ClinicalWorkflowRequest,
):
    try:
        logger.info("Clinical workflow API request received")

        result = await workflow_service.run_workflow(request)

        logger.info("Clinical workflow API request completed")

        return result

    except Exception as exc:
        logger.exception("Clinical workflow API failed")
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )