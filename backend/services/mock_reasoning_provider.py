import json
from typing import Dict, Any

from backend.services.reasoning_provider import ReasoningProvider


class MockReasoningProvider(ReasoningProvider):
    """
    A deterministic mock reasoning provider for testing.
    Does not require llama.cpp or any external model.
    """

    async def generate_reasoning(
        self, prompt: str
    ) -> str:
        """
        Returns a hardcoded, deterministic string resembling a valid MedGemma response.
        """
        # We assume the prompt requests reasoning for candidates.
        # We provide a dummy structured JSON response that the parser can successfully parse.
        
        mock_response = {
            "candidate_reasoning": [
                {
                    "rank": 1,
                    "disease": "Acute Bronchitis",
                    "supporting_findings": ["Cough", "Mild fever"],
                    "conflicting_findings": ["No sputum"],
                    "missing_information": ["Chest X-Ray"],
                    "rationale": "Mock reasoning for acute bronchitis."
                }
            ],
            "important_uncertainties": ["Exact duration of cough"],
            "red_flags_to_review": ["High fever"],
            "next_information_needed": ["Sputum culture"],
            "reasoning_summary": "Mock reasoning summary.",
            "limitations": ["Mock limitations"],
            "requires_doctor_review": True
        }
        
        # Wrap it in markdown fences like a real LLM might.
        return f"```json\n{json.dumps(mock_response, indent=2)}\n```"
