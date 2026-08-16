from typing import Optional
from pydantic import BaseModel, Field

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    medical_history_summary: Optional[str] = None

class PatientUpdate(BaseModel):
    medical_history_summary: Optional[str] = None

class PatientResponse(PatientCreate):
    id: str
    created_at: str
    updated_at: str
