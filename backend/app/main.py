import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../..", "backend")
    )
)

from fastapi import Depends, FastAPI

from backend.app.api.prediction import router as prediction_router
from backend.app.api.reasoning import router as reasoning_router
from backend.app.api.verification import router as verification_router
from backend.app.api.treatment import router as treatment_router
from backend.app.api.workflow import router as workflow_router
from backend.app.api.assessment import router as assessment_router
from backend.app.api.auth import router as auth_router
from backend.app.auth import require_clinician


app = FastAPI(title="MedIntel API", version="1.0")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "MedIntel API",
        "version": "1.0",
    }


app.include_router(
    auth_router,
    prefix="/api/v1",
)

clinician_dependencies = [
    Depends(require_clinician),
]

app.include_router(
    prediction_router,
    prefix="/api/v1",
    dependencies=clinician_dependencies,
)
app.include_router(
    reasoning_router,
    prefix="/api/v1/clinical",
    dependencies=clinician_dependencies,
)
app.include_router(
    verification_router,
    prefix="/api/v1/clinical",
    dependencies=clinician_dependencies,
)
app.include_router(
    treatment_router,
    prefix="/api/v1/clinical",
    dependencies=clinician_dependencies,
)
app.include_router(
    workflow_router,
    prefix="/api/v1/clinical",
    dependencies=clinician_dependencies,
)
app.include_router(
    assessment_router,
    prefix="/api/v1/clinical",
    dependencies=clinician_dependencies,
)
