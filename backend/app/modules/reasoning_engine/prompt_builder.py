import os

from backend.app.config.settings import settings


class PromptBuilder:
    """
    Builds the final prompt by injecting deterministic clinical context
    into the selected reasoning prompt template.
    """

    _SAFETY_COMPLIANCE_RETRY_INSTRUCTIONS = """
SAFETY COMPLIANCE RETRY

The previous generated response did not pass the deterministic
MedIntel safety validator.

This is exactly one compliance-correction regeneration.
Do not perform a new differential diagnosis.

Mandatory rules:

1. Return exactly one candidate_reasoning entry for every ranked
   differential candidate supplied in the clinical context.
2. Do not add or remove candidates.
3. Preserve every candidate rank exactly.
4. Preserve every candidate disease name exactly.
5. requires_doctor_review MUST remain true.
6. Do not provide a final diagnosis or claim diagnostic certainty.
7. Do not use authoritative diagnostic wording such as:
   - "most likely diagnosis"
   - "diagnosis is"
   - "confirms the diagnosis"
   - "confirm the diagnosis"
   - "supports this conclusion"
   - "supports the conclusion"
8. Continue to use only the supplied clinical evidence and
   knowledge-base context.
9. Do not infer absent patient findings.
10. Return only structured output matching the required
    ClinicalReasoningResponse schema.

Correct only the safety-compliance problem.
Do not mention this retry or the previous rejected response.
""".strip()

    @staticmethod
    def build_prompt(context_str: str) -> str:
        prompt_version = settings.REASONING_PROMPT_VERSION

        prompt_path = os.path.join(
            os.getcwd(),
            "prompts",
            f"{prompt_version}.txt",
        )

        if not os.path.exists(prompt_path):
            raise FileNotFoundError(
                f"Prompt template {prompt_path} not found."
            )

        with open(
            prompt_path,
            "r",
            encoding="utf-8",
        ) as prompt_file:
            template = prompt_file.read()

        return template.replace(
            "{{CONTEXT}}",
            context_str,
        )

    @classmethod
    def build_safety_retry_prompt(
        cls,
        base_prompt: str,
    ) -> str:
        """
        Append deterministic compliance instructions for the single
        application-level safety retry.

        The rejected model response is intentionally not included.
        """

        if not isinstance(base_prompt, str) or not base_prompt.strip():
            raise ValueError(
                "Base reasoning prompt is empty."
            )

        return (
            base_prompt.rstrip()
            + "\n\n"
            + cls._SAFETY_COMPLIANCE_RETRY_INSTRUCTIONS
        )
