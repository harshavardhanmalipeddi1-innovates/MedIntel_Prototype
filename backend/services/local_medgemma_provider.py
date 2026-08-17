import asyncio
import logging

import httpx

from backend.app.config.settings import settings
from backend.app.schemas.reasoning_schema import ClinicalReasoningResponse
from backend.services.reasoning_provider import (
    ReasoningInvalidResponseError,
    ReasoningProvider,
    ReasoningUnavailableError,
)


logger = logging.getLogger(__name__)


class LocalMedGemmaProvider(ReasoningProvider):
    """
    Clinical reasoning provider backed by the local llama.cpp server.

    Generation is constrained by the MedIntel ClinicalReasoningResponse
    JSON schema. Raw prompts and responses are never logged because they
    may contain clinical information.
    """

    def __init__(self):
        self.base_url = settings.MEDGEMMA_BASE_URL.rstrip("/")
        self.timeout = settings.MEDGEMMA_TIMEOUT_SECONDS
        self.max_retries = max(0, settings.MEDGEMMA_MAX_RETRIES)
        self.model_id = settings.LOCAL_MEDGEMMA_MODEL_ID

    async def generate_reasoning(self, prompt: str) -> str:
        response_schema = ClinicalReasoningResponse.model_json_schema()

        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a clinical reasoning support component "
                        "inside MedIntel. Return only structured JSON matching "
                        "the supplied schema. Do not expose chain-of-thought. "
                        "Do not make a final diagnosis or prescription."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.0,
            "max_tokens": 384,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "clinical_reasoning_response",
                    "schema": response_schema,
                },
            },
        }

        last_error = None
        total_attempts = self.max_retries + 1

        for attempt in range(total_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/chat/completions",
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()

                try:
                    choice = data["choices"][0]
                    content = choice["message"]["content"]
                    finish_reason = choice.get("finish_reason")
                except (KeyError, IndexError, TypeError) as exc:
                    raise ReasoningInvalidResponseError(
                        "Malformed response structure from Local MedGemma."
                    ) from exc

                if finish_reason == "length":
                    raise ReasoningInvalidResponseError(
                        "Local MedGemma response hit the generation token limit."
                    )

                if not isinstance(content, str) or not content.strip():
                    raise ReasoningInvalidResponseError(
                        "Local MedGemma returned empty response content."
                    )

                return content

            except ReasoningInvalidResponseError:
                raise

            except httpx.TimeoutException as exc:
                last_error = exc

            except httpx.RequestError as exc:
                last_error = exc

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500:
                    raise ReasoningUnavailableError(
                        "Local MedGemma server rejected the request."
                    ) from exc
                last_error = exc

            if attempt < self.max_retries:
                await asyncio.sleep(0.25)

        logger.error(
            "Local MedGemma unavailable after %d attempt(s).",
            total_attempts,
        )
        raise ReasoningUnavailableError(
            f"Local MedGemma unavailable after {total_attempts} attempt(s)."
        ) from last_error
