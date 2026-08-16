import re
from typing import Iterator

from backend.app.config.settings import settings
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
)


class SafetyValidator:
    """
    Ensures model outputs do not violate clinical safety boundaries.
    """

    _AUTHORITATIVE_DIAGNOSTIC_PATTERNS = (
        re.compile(r"\bmost likely diagnosis\b", re.IGNORECASE),
        re.compile(
            r"\bdiagnosis is\b(?!\s+(?:not|uncertain|unconfirmed))",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bconfirms?\s+(?:the\s+)?diagnosis\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bsupports?\s+(?:this|the)\s+conclusion\b",
            re.IGNORECASE,
        ),
    )

    @staticmethod
    def _response_text(
        response: ClinicalReasoningResponse,
    ) -> Iterator[str]:
        for candidate in response.candidate_reasoning:
            yield from candidate.supporting_findings
            yield from candidate.conflicting_findings
            yield from candidate.missing_information
            yield candidate.rationale

        yield from response.important_uncertainties
        yield from response.red_flags_to_review
        yield from response.next_information_needed
        yield response.reasoning_summary
        yield from response.limitations

    @classmethod
    def _validate_non_authoritative_language(
        cls,
        response: ClinicalReasoningResponse,
    ) -> None:
        for text in cls._response_text(response):
            for pattern in cls._AUTHORITATIVE_DIAGNOSTIC_PATTERNS:
                if pattern.search(text):
                    raise ValueError(
                    "Safety Violation: Authoritative diagnostic wording detected "
                    f"(pattern={pattern.pattern!r})."
                )

    @classmethod
    def validate(
        cls,
        request: ClinicalReasoningRequest,
        response: ClinicalReasoningResponse,
    ):
        # Doctor review can never be bypassed.
        if response.requires_doctor_review is not True:
            raise ValueError(
                "Safety Violation: requires_doctor_review was bypassed."
            )

        expected_candidates = request.differential[
            : settings.REASONING_MAX_CANDIDATES
        ]
        reasoning_candidates = response.candidate_reasoning

        if len(reasoning_candidates) != len(expected_candidates):
            raise ValueError(
                "Safety Violation: Number of candidates was changed by the model."
            )

        for original, generated in zip(
            expected_candidates,
            reasoning_candidates,
        ):
            if generated.rank != original.rank:
                raise ValueError(
                    "Safety Violation: Candidate rank changed "
                    f"from {original.rank} to {generated.rank}."
                )

            if generated.disease.lower() != original.disease.lower():
                raise ValueError(
                    "Safety Violation: Candidate disease changed "
                    f"from {original.disease} to {generated.disease}."
                )

        cls._validate_non_authoritative_language(response)

        return True
