import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ThresholdEngine:
    """
    Filters diseases that have probabilities below the configured minimum threshold.
    """
    
    def __init__(self, min_probability: float = 0.10):
        self.min_probability = min_probability
        logger.info(f"ThresholdEngine initialized with min_probability={self.min_probability}")
        
    def filter(self, predictions: Dict[str, float]) -> Dict[str, float]:
        """
        Discards diseases with probability below the minimum threshold.
        """
        filtered = {
            disease: prob for disease, prob in predictions.items()
            if prob >= self.min_probability
        }
        logger.debug(f"Threshold filtering complete. Remaining diseases: {len(filtered)}")
        return filtered
