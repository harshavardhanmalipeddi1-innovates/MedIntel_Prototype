import logging

logger = logging.getLogger(__name__)

class ConfidenceEngine:
    """
    Evaluates probabilities and maps them to qualitative confidence labels.
    """
    
    def __init__(self, high_threshold: float = 0.85, medium_threshold: float = 0.60):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        logger.info(f"ConfidenceEngine initialized with high={self.high_threshold}, medium={self.medium_threshold}")
        
    def evaluate(self, probability: float) -> str:
        """
        Maps a probability float to 'High', 'Medium', or 'Low' confidence.
        """
        if probability >= self.high_threshold:
            return "High"
        elif probability >= self.medium_threshold:
            return "Medium"
        else:
            return "Low"
