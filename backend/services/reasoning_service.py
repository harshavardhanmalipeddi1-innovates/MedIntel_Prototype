import logging

from pydantic import ValidationError

from backend.app.config.settings import settings
from backend.app.modules.reasoning_engine.context_builder import ContextBuilder
from backend.app.modules.reasoning_engine.evidence_semantic_normalizer import (
    EvidenceSemanticNormalizer,
)
from backend.app.modules.reasoning_engine.prompt_builder import PromptBuilder
from backend.app.modules.reasoning_engine.response_parser import ResponseParser
from backend.app.modules.reasoning_engine.safety_validator import SafetyValidator
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
)
from backend.services.local_medgemma_provider import LocalMedGemmaProvider
from backend.services.mock_reasoning_provider import MockReasoningProvider
from backend.services.reasoning_provider import ReasoningProviderError


logger = logging.getLogger(__name__)


class ReasoningService:
    """
    Coordinates the clinical reasoning process while enforcing the
    deterministic MedIntel safety gates.
    """

    def __init__(self):
        provider_name = settings.AI_PROVIDER.strip().lower()

        if provider_name == "local":
            self.provider = LocalMedGemmaProvider()
        elif provider_name == "mock":
            self.provider = MockReasoningProvider()
        else:
            raise ValueError(
                f"Unsupported AI_PROVIDER: {settings.AI_PROVIDER!r}. "
                "Expected 'local' or 'mock'."
            )

    async def _generate_response_object(
        self,
        request: ClinicalReasoningRequest,
        prompt: str,
    ) -> ClinicalReasoningResponse:
        """
        Perform one provider generation followed by parsing, schema
        validation, and deterministic evidence normalization.

        Safety validation is intentionally NOT performed here so the
        caller can distinguish a safety failure from parser/schema/
        provider failures.
        """

        raw_response = await self.provider.generate_reasoning(
            prompt
        )

        parsed_json = ResponseParser.parse(
            raw_response
        )

        response_obj = ClinicalReasoningResponse(
            **parsed_json
        )

        response_obj = EvidenceSemanticNormalizer.normalize(
            request,
            response_obj,
        )

        return response_obj

    async def generate_reasoning(
        self,
        request: ClinicalReasoningRequest,
    ) -> ClinicalReasoningResponse:
        """
        Execute the clinical reasoning pipeline.

        A deterministic SafetyValidator failure is allowed exactly one
        application-level compliance regeneration. Provider, parsing,
        and schema failures do not trigger that retry.
        """

        if not settings.AI_REASONING_ENABLED:
            return self._build_degraded_response(
                request,
                "AI Reasoning is disabled in configuration.",
            )

        try:
            # ------------------------------------------------------
            # 1. Build deterministic context and normal prompt
            # ------------------------------------------------------
            context_str = ContextBuilder.build_context(
                request
            )

            prompt = PromptBuilder.build_prompt(
                context_str
            )

            # ------------------------------------------------------
            # 2. First generation
            # ------------------------------------------------------
            response_obj = (
                await self._generate_response_object(
                    request,
                    prompt,
                )
            )

            # ------------------------------------------------------
            # 3. First deterministic safety validation
            # ------------------------------------------------------
            try:
                SafetyValidator.validate(
                    request,
                    response_obj,
                )

            except ValueError:
                logger.warning(
                    "Clinical reasoning output failed deterministic "
                    "safety validation; executing one compliance retry."
                )

                # --------------------------------------------------
                # 4. Exactly one application-level compliance retry
                # --------------------------------------------------
                retry_prompt = (
                    PromptBuilder.build_safety_retry_prompt(
                        prompt
                    )
                )

                retry_response_obj = (
                    await self._generate_response_object(
                        request,
                        retry_prompt,
                    )
                )

                # --------------------------------------------------
                # 5. Retry must pass the SAME SafetyValidator
                # --------------------------------------------------
                try:
                    SafetyValidator.validate(
                        request,
                        retry_response_obj,
                    )

                except ValueError:
                    logger.warning(
                        "Clinical reasoning compliance retry also "
                        "failed deterministic safety validation."
                    )

                    return self._build_degraded_response(
                        request,
                        (
                            "Clinical reasoning output failed safety "
                            "validation after one compliance retry."
                        ),
                    )

                logger.info(
                    "Clinical reasoning compliance retry passed "
                    "deterministic safety validation."
                )

                return retry_response_obj

            return response_obj

        except ReasoningProviderError:
            logger.warning(
                "Clinical reasoning provider unavailable."
            )

            return self._build_degraded_response(
                request,
                "Local clinical reasoning provider is unavailable.",
            )

        except ValidationError:
            logger.warning(
                "Clinical reasoning output failed schema validation."
            )

            return self._build_degraded_response(
                request,
                "Clinical reasoning output failed schema validation.",
            )

        except ValueError:
            # ResponseParser also raises ValueError. Because the
            # SafetyValidator calls are handled explicitly above,
            # reaching this block does NOT trigger a compliance retry.
            logger.warning(
                "Clinical reasoning output failed parsing."
            )

            return self._build_degraded_response(
                request,
                "Clinical reasoning output failed parsing.",
            )

        except Exception:
            logger.exception(
                "Unexpected clinical reasoning service failure."
            )

            return self._build_degraded_response(
                request,
                "Clinical reasoning is temporarily unavailable.",
            )

    def _build_degraded_response(
        self,
        request: ClinicalReasoningRequest,
        reason: str,
    ) -> ClinicalReasoningResponse:
        """
        Create a safe degraded response while preserving the existing
        upstream differential and injecting no AI diagnosis.
        """

        return ClinicalReasoningResponse(
            candidate_reasoning=[],
            reasoning_summary=(
                f"Reasoning unavailable: {reason}"
            ),
            limitations=[
                (
                    "AI Reasoning engine was unavailable "
                    "or failed validation."
                ),
                reason,
            ],
            requires_doctor_review=True,
        )
