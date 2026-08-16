import json
from typing import Any, Dict


class ResponseParser:
    """
    Extracts structured clinical reasoning JSON from model output.

    MedGemma may emit internal reasoning text before its final answer.
    This parser never exposes that text. It searches for independently
    decodable JSON objects and returns only the final valid JSON object.
    """

    @staticmethod
    def parse(raw_response: str) -> Dict[str, Any]:
        if not isinstance(raw_response, str) or not raw_response.strip():
            raise ValueError("Reasoning response was empty.")

        text = raw_response.strip()

        # Fast path: response is already pure JSON.
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # MedGemma can place thought/reasoning text around the final JSON.
        # Try each opening brace independently using Python's JSON decoder.
        decoder = json.JSONDecoder()
        objects = []

        for index, char in enumerate(text):
            if char != "{":
                continue

            try:
                obj, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue

            if isinstance(obj, dict):
                objects.append(obj)

        if not objects:
            raise ValueError(
                "No valid JSON object found in reasoning response."
            )

        # The final independently decodable object is treated as the
        # model's final structured answer. Subsequent Pydantic and safety
        # validation determine whether it is acceptable.
        return objects[-1]
