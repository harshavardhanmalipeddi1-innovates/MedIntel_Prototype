from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

class VerificationStep(StrictSchema):
    candidate_disease: str
    reason: str
    priority: Literal["low", "medium", "high", "critical"]
    category: Literal["physical_examination", "laboratory", "imaging", "history", "other"]
    supporting_context: Optional[str] = None
    is_red_flag: bool = False
    requires_doctor_review: Literal[True] = True

class ClinicalVerificationResponse(StrictSchema):
    suggested_steps: List[VerificationStep] = Field(default_factory=list)
    missing_information_summary: List[str] = Field(default_factory=list)
    requires_doctor_review: Literal[True] = True
