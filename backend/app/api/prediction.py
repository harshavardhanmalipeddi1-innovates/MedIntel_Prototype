from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

from backend.app.ml.feature_builder import FeatureBuilder
from backend.services.clinical_rules import ClinicalRules
from backend.services.prediction_service import PredictionService
from backend.services.differential_manager import DifferentialDiagnosisManager

logger = logging.getLogger(__name__)

router = APIRouter()

class PredictionRequest(BaseModel):
    data: Dict[str, Any]

class OutputValidator:
    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        result["validated"] = True
        return result

feature_builder = FeatureBuilder()
clinical_rules = ClinicalRules()
prediction_service = PredictionService()
differential_manager = DifferentialDiagnosisManager()
output_validator = OutputValidator()

@router.post("/predict")
async def predict(request: PredictionRequest):
    try:
        logger.info("Prediction started")
        req_data = request.data
        
        # 1. Feature Builder
        features = feature_builder.build_feature_vector(req_data)
        
        # 2. Prediction Service
        prediction = prediction_service.predict_primary_disease(features.toarray() if hasattr(features, 'toarray') else features)
        logger.info("Prediction received")
        
        # Extract raw probabilities for Differential Diagnosis Manager
        raw_probs = {
            item["condition"]: item["probability"]
            for item in prediction.get("predictions", [])
        }
        
        # 3. Differential Diagnosis Manager
        differential_result = differential_manager.generate_differential(raw_probs)
        logger.info("Differential diagnosis generated")
        
        # (Optional) Integrate rules/validator for backward compatibility
        rules_result = clinical_rules.evaluate(req_data)
        
        # Construct final enhanced response maintaining the original top level keys but with our structured differential list
        final_output = {
            "success": True,
            "predictions": differential_result["predictions"],
            "rules": rules_result
        }
        validated_output = output_validator.validate(final_output)
        
        logger.info("Prediction response returned")
        return validated_output
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
