import logging
from typing import Dict, Any, List

from backend.app.config.settings import settings
from backend.services.ranking_engine import RankingEngine
from backend.services.threshold_engine import ThresholdEngine
from backend.services.confidence_engine import ConfidenceEngine
from backend.services.knowledge_base import KnowledgeBaseService

logger = logging.getLogger(__name__)

class DifferentialDiagnosisManager:
    """
    Coordinates the Differential Diagnosis pipeline.
    """
    
    def __init__(self):
        self.ranking_engine = RankingEngine(top_k=settings.TOP_K)
        self.threshold_engine = ThresholdEngine(min_probability=settings.MIN_PROBABILITY)
        self.confidence_engine = ConfidenceEngine(
            high_threshold=settings.HIGH_CONFIDENCE_THRESHOLD,
            medium_threshold=settings.MEDIUM_CONFIDENCE_THRESHOLD
        )
        self.knowledge_base = KnowledgeBaseService()
        logger.info("DifferentialDiagnosisManager initialized")
        
    def generate_differential(self, raw_predictions: Dict[str, float]) -> Dict[str, Any]:
        """
        Takes raw disease probabilities and returns a structured differential diagnosis.
        """
        logger.info("Differential diagnosis generation started")
        
        # 1. Threshold Filtering
        filtered_predictions = self.threshold_engine.filter(raw_predictions)
        logger.debug("Threshold filtering complete")
        
        # 2. Ranking
        ranked_predictions = self.ranking_engine.rank(filtered_predictions)
        logger.debug("Ranking complete")
        
        # 3. Confidence Mapping & Knowledge Base Lookup
        results = []
        for item in ranked_predictions:
            confidence = self.confidence_engine.evaluate(item["probability"])
            kb_entry = self.knowledge_base.get_disease(item["disease"])
            knowledge_dict = kb_entry.model_dump() if kb_entry else None
            if not knowledge_dict:
                logger.info(f"Knowledge unavailable for disease: {item['disease']}")
                
            results.append({
                "rank": item["rank"],
                "disease": item["disease"],
                "probability": item["probability"],
                "confidence": confidence,
                "knowledge": knowledge_dict
            })
            
        logger.info("Differential diagnosis generated successfully")
        
        return {
            "success": True,
            "predictions": results
        }
