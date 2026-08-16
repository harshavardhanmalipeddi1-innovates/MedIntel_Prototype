from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

class TreatmentConsideration(StrictSchema):
    candidate_disease: str
    consideration: str
    rationale: str
    warnings: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    contraindication_concern: bool = False

class TreatmentDraftResponse(StrictSchema):
    considerations: List[TreatmentConsideration] = Field(default_factory=list)
    general_cautions: List[str] = Field(default_factory=list)
    
    status: Literal["AI_GENERATED_DRAFT"] = "AI_GENERATED_DRAFT"
    requires_doctor_review: Literal[True] = True
    doctor_approval_status: Literal["PENDING"] = "PENDING"
