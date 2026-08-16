import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class RankingEngine:
    """
    Ranks disease predictions based on probability.
    """
    
    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        logger.info(f"RankingEngine initialized with top_k={self.top_k}")
        
    def rank(self, predictions: Dict[str, float]) -> List[Dict]:
        """
        Takes a dictionary of disease probabilities and returns a sorted, ranked list.
        """
        sorted_predictions = sorted(predictions.items(), key=lambda item: item[1], reverse=True)
        
        ranked_list = []
        for rank, (disease, probability) in enumerate(sorted_predictions[:self.top_k], start=1):
            ranked_list.append({
                "rank": rank,
                "disease": disease,
                "probability": probability
            })
            
        logger.debug(f"Ranking completed. Ranked {len(ranked_list)} diseases.")
        return ranked_list
