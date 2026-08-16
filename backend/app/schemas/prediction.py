from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.schemas.knowledge_schema import DiseaseKnowledge

class PredictionRequest(BaseModel):
    patient_data: Dict[str, Any]

class DifferentialItem(BaseModel):
    rank: int
    disease: str
    probability: float
    confidence: str
    knowledge: Optional[DiseaseKnowledge] = None

class PredictionResponse(BaseModel):
    predictions: List[DifferentialItem]
    model: str
    status: str
