from typing import List, Optional
from pydantic import BaseModel, Field

class ClinicalReference(BaseModel):
    title: str
    organization: str
    year: Optional[str] = None
    url: Optional[str] = None

class DiseaseKnowledge(BaseModel):
    disease_id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
    description: str
    body_system: Optional[str] = None
    common_symptoms: List[str] = Field(default_factory=list)
    associated_symptoms: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    physical_examination: List[str] = Field(default_factory=list)
    recommended_investigations: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    contraindications: List[str] = Field(default_factory=list)
    differential_diagnoses: List[str] = Field(default_factory=list)
    icd10_codes: List[str] = Field(default_factory=list)
    clinical_references: List[ClinicalReference] = Field(default_factory=list)
    knowledge_version: str
