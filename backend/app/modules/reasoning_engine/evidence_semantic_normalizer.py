import re
from typing import Any

from backend.app.modules.reasoning_engine.context_builder import ContextBuilder
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
)


class EvidenceSemanticNormalizer:
    """
    Deterministically converts raw model evidence identifiers in the
    doctor-facing reasoning response into human-readable DDXPlus metadata.

    This layer does not change:
    - candidate identity
    - rank
    - probability
    - confidence
    - rationale
    - upstream ML features

    It also prevents already-supplied evidence from being represented as
    missing information.
    """

    _RAW_EVIDENCE_PATTERN = re.compile(
        r"^(?:INITIAL::)?E_\d+(?:_@_.+)?$"
    )

    _NO_MISSING_SENTINELS = {
        "none",
        "none.",
        "no information is missing",
        "no information is missing.",
        "no missing information",
        "no missing information.",
        "nothing is missing",
        "nothing is missing.",
    }

    @classmethod
    def _metadata_question(cls, code: str) -> str | None:
        metadata = ContextBuilder._load_evidence_metadata()
        details = metadata.get(code)

        if not isinstance(details, dict):
            return None

        question = details.get("question_en")

        if not isinstance(question, str):
            return None

        question = question.strip()

        return question or None

    @classmethod
    def _value_meaning(
        cls,
        code: str,
        encoded_value: str | None,
    ) -> str | None:
        if encoded_value is None:
            return None

        metadata = ContextBuilder._load_evidence_metadata()
        details = metadata.get(code)

        if not isinstance(details, dict):
            return None

        value_meaning = details.get("value_meaning")

        if not isinstance(value_meaning, dict):
            return None

        meaning = value_meaning.get(encoded_value)

        if meaning is None:
            return None

        return str(meaning).strip() or None

    @classmethod
    def _humanize_raw_token(
        cls,
        text: str,
        observed_by_code: dict[str, str],
        observed_by_token: dict[str, str],
    ) -> str:
        stripped = text.strip()

        if stripped in observed_by_token:
            return observed_by_token[stripped]

        code, encoded_value, _ = ContextBuilder._decode_evidence_token(
            stripped
        )

        if code in observed_by_code:
            return observed_by_code[code]

        if not cls._RAW_EVIDENCE_PATTERN.fullmatch(stripped):
            return text

        question = cls._metadata_question(code)

        if question is None:
            return text

        value_meaning = cls._value_meaning(
            code,
            encoded_value,
        )

        if value_meaning:
            return (
                f"{question} "
                f"Selected response: {value_meaning}"
            )

        if encoded_value is not None:
            return (
                f"{question} "
                f"Selected encoded response: {encoded_value}"
            )

        return question

    @classmethod
    def _observed_maps(
        cls,
        request: ClinicalReasoningRequest,
    ) -> tuple[
        dict[str, str],
        dict[str, str],
        set[str],
        set[str],
    ]:
        semantic = ContextBuilder._build_semantic_evidence(
            request.patient_context
        )

        observed_by_code: dict[str, str] = {}
        observed_by_token: dict[str, str] = {}
        supplied_codes: set[str] = set()
        supplied_meanings: set[str] = set()

        observed = semantic.get(
            "Observed_Clinical_Evidence",
            [],
        )

        for item in observed:
            if not isinstance(item, dict):
                continue

            code = str(item.get("Code", "")).strip()
            token = str(
                item.get("Original_Token", "")
            ).strip()
            question = str(
                item.get("Clinical_Meaning", "")
            ).strip()
            source = str(
                item.get("Source", "")
            ).strip()

            if not code or not question:
                continue

            encoded_value = item.get("Encoded_Value")
            value_meaning = item.get("Value_Meaning")

            if source == "initial_evidence":
                label = (
                    f"Observed initial evidence: {question}"
                )
            elif value_meaning:
                label = (
                    f"Observed response: {question} "
                    f"Selected response: {value_meaning}"
                )
            elif encoded_value is not None:
                label = (
                    f"Observed response: {question} "
                    f"Selected encoded response: {encoded_value}"
                )
            else:
                label = (
                    f"Observed positive response: {question}"
                )

            observed_by_code[code] = label

            if token:
                observed_by_token[token] = label

            supplied_codes.add(code)
            supplied_meanings.add(question.casefold())
            supplied_meanings.add(label.casefold())

        answered_codes = semantic.get(
            "Explicitly_Answered_Question_Codes",
            [],
        )

        if isinstance(answered_codes, list):
            for raw_code in answered_codes:
                code = str(raw_code).strip()

                if not code:
                    continue

                supplied_codes.add(code)

                question = cls._metadata_question(code)

                if question:
                    supplied_meanings.add(
                        question.casefold()
                    )

        return (
            observed_by_code,
            observed_by_token,
            supplied_codes,
            supplied_meanings,
        )

    @classmethod
    def normalize(
        cls,
        request: ClinicalReasoningRequest,
        response: ClinicalReasoningResponse,
    ) -> ClinicalReasoningResponse:
        (
            observed_by_code,
            observed_by_token,
            supplied_codes,
            supplied_meanings,
        ) = cls._observed_maps(request)

        payload: dict[str, Any] = response.model_dump()

        for candidate in payload.get(
            "candidate_reasoning",
            [],
        ):
            candidate["supporting_findings"] = [
                cls._humanize_raw_token(
                    str(item),
                    observed_by_code,
                    observed_by_token,
                )
                for item in candidate.get(
                    "supporting_findings",
                    [],
                )
            ]

            candidate["conflicting_findings"] = [
                cls._humanize_raw_token(
                    str(item),
                    observed_by_code,
                    observed_by_token,
                )
                for item in candidate.get(
                    "conflicting_findings",
                    [],
                )
            ]

            normalized_missing: list[str] = []

            for raw_item in candidate.get(
                "missing_information",
                [],
            ):
                item = str(raw_item).strip()

                if not item:
                    continue

                if (
                    item.casefold()
                    in cls._NO_MISSING_SENTINELS
                ):
                    continue

                if item.casefold() in supplied_meanings:
                    continue

                if cls._RAW_EVIDENCE_PATTERN.fullmatch(
                    item
                ):
                    code, _, _ = (
                        ContextBuilder._decode_evidence_token(
                            item
                        )
                    )

                    if code in supplied_codes:
                        continue

                normalized_missing.append(
                    cls._humanize_raw_token(
                        item,
                        observed_by_code,
                        observed_by_token,
                    )
                )

            candidate[
                "missing_information"
            ] = normalized_missing

        return ClinicalReasoningResponse(**payload)
