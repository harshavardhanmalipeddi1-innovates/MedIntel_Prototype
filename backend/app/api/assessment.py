import logging

from fastapi import APIRouter, HTTPException

from backend.app.schemas.assessment_schema import (
    AssessmentPrepareRequest,
    AssessmentPrepareResponse,
    AssessmentQuestionnaireResponse,
)
from backend.services.assessment_service import AssessmentService


logger = logging.getLogger(__name__)
router = APIRouter()
assessment_service = AssessmentService()


@router.get(
    "/assessment/questionnaire",
    response_model=AssessmentQuestionnaireResponse,
)
async def get_assessment_questionnaire():
    try:
        return assessment_service.get_questionnaire()

    except Exception as exc:
        logger.exception("Assessment questionnaire generation failed")
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post(
    "/assessment/prepare",
    response_model=AssessmentPrepareResponse,
)
async def prepare_assessment(
    request: AssessmentPrepareRequest,
):
    try:
        answers = [
            answer.model_dump()
            for answer in request.answers
        ]

        return assessment_service.prepare_assessment(
            age=request.age,
            sex=request.sex,
            initial_evidence=request.initial_evidence,
            answers=answers,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        logger.exception("Assessment preparation failed")
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
