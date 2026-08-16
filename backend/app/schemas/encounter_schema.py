from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

class EncounterCreate(BaseModel):
    patient_id: str
    doctor_id: str
    symptoms: List[str] = Field(default_factory=list)
    history: Optional[str] = None
    vitals: Dict[str, Any] = Field(default_factory=dict)
    physical_examination: Optional[str] = None

class EncounterResponse(EncounterCreate):
    id: str
    created_at: str
    updated_at: str
    ai_prediction_results: Optional[Dict[str, Any]] = None
    ai_reasoning_results: Optional[Dict[str, Any]] = None
    ai_verification_results: Optional[Dict[str, Any]] = None
    ai_treatment_draft: Optional[Dict[str, Any]] = None
    doctor_confirmed_outcome: Optional[Dict[str, Any]] = None
