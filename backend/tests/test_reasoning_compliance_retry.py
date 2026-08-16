import json

import pytest

from backend.app.config.settings import settings
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ReasoningDifferentialItem,
    ClinicalRuleResult,
)
from backend.services.reasoning_provider import (
    ReasoningUnavailableError,
)
from backend.services.reasoning_service import ReasoningService


class SequenceProvider:
    """
    Deterministic test provider returning responses in sequence.
    """

    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    @property
    def call_count(self):
        return len(self.prompts)

    async def generate_reasoning(
        self,
        prompt: str,
    ) -> str:
        self.prompts.append(prompt)

        if not self.responses:
            raise AssertionError(
                "Provider called more times than expected."
            )

        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


def _request() -> ClinicalReasoningRequest:
    return ClinicalReasoningRequest(
        patient_context={
            "age": 45,
            "sex": "M",
        },
        rules=ClinicalRuleResult(),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Pneumonia",
                probability=0.8,
                confidence="High",
            )
        ],
    )


def _payload(
    *,
    summary: str = (
        "Further clinical verification is required."
    ),
    disease: str = "Pneumonia",
):
    return {
        "candidate_reasoning": [
            {
                "rank": 1,
                "disease": disease,
                "supporting_findings": [
                    "Cough",
                ],
                "conflicting_findings": [],
                "missing_information": [],
                "rationale": (
                    "Requires clinician verification."
                ),
            }
        ],
        "important_uncertainties": [],
        "red_flags_to_review": [],
        "next_information_needed": [],
        "reasoning_summary": summary,
        "limitations": [],
        "requires_doctor_review": True,
    }


def _json_response(**kwargs) -> str:
    return json.dumps(
        _payload(**kwargs)
    )


def _service(
    monkeypatch,
    responses,
):
    monkeypatch.setattr(
        settings,
        "AI_PROVIDER",
        "mock",
    )

    monkeypatch.setattr(
        settings,
        "AI_REASONING_ENABLED",
        True,
    )

    service = ReasoningService()

    service.provider = SequenceProvider(
        responses
    )

    return service


@pytest.mark.asyncio
async def test_first_safe_response_does_not_retry(
    monkeypatch,
):
    service = _service(
        monkeypatch,
        [
            _json_response(),
        ],
    )

    response = await service.generate_reasoning(
        _request()
    )

    assert service.provider.call_count == 1

    assert (
        response.reasoning_summary
        == "Further clinical verification is required."
    )

    assert (
        "SAFETY COMPLIANCE RETRY"
        not in service.provider.prompts[0]
    )


@pytest.mark.asyncio
async def test_safety_failure_retries_once_and_passes(
    monkeypatch,
):
    unsafe = _json_response(
        summary=(
            "The most likely diagnosis is Pneumonia."
        )
    )

    safe = _json_response()

    service = _service(
        monkeypatch,
        [
            unsafe,
            safe,
        ],
    )

    response = await service.generate_reasoning(
        _request()
    )

    assert service.provider.call_count == 2

    assert (
        response.reasoning_summary
        == "Further clinical verification is required."
    )

    first_prompt = service.provider.prompts[0]
    retry_prompt = service.provider.prompts[1]

    assert (
        "SAFETY COMPLIANCE RETRY"
        not in first_prompt
    )

    assert (
        "SAFETY COMPLIANCE RETRY"
        in retry_prompt
    )

    assert (
        "Preserve every candidate rank exactly."
        in retry_prompt
    )

    assert (
        "Preserve every candidate disease name exactly."
        in retry_prompt
    )

    assert (
        "requires_doctor_review MUST remain true"
        in retry_prompt
    )

    # The rejected model output itself must never be copied into
    # the retry prompt.
    assert (
        "The most likely diagnosis is Pneumonia."
        not in retry_prompt
    )


@pytest.mark.asyncio
async def test_second_safety_failure_degrades_after_one_retry(
    monkeypatch,
):
    unsafe = _json_response(
        summary=(
            "The most likely diagnosis is Pneumonia."
        )
    )

    service = _service(
        monkeypatch,
        [
            unsafe,
            unsafe,
        ],
    )

    response = await service.generate_reasoning(
        _request()
    )

    assert service.provider.call_count == 2

    assert response.candidate_reasoning == []

    assert (
        "after one compliance retry"
        in response.reasoning_summary.lower()
    )

    assert response.requires_doctor_review is True


@pytest.mark.asyncio
async def test_parser_failure_does_not_trigger_retry(
    monkeypatch,
):
    service = _service(
        monkeypatch,
        [
            "this is not JSON",
        ],
    )

    response = await service.generate_reasoning(
        _request()
    )

    assert service.provider.call_count == 1

    assert response.candidate_reasoning == []

    assert (
        "failed parsing"
        in response.reasoning_summary.lower()
    )


@pytest.mark.asyncio
async def test_schema_failure_does_not_trigger_retry(
    monkeypatch,
):
    invalid = _payload()
    invalid["unexpected_field"] = "reject me"

    service = _service(
        monkeypatch,
        [
            json.dumps(invalid),
        ],
    )

    response = await service.generate_reasoning(
        _request()
    )

    assert service.provider.call_count == 1

    assert response.candidate_reasoning == []

    assert (
        "schema validation"
        in response.reasoning_summary.lower()
    )


@pytest.mark.asyncio
async def test_provider_failure_does_not_trigger_retry(
    monkeypatch,
):
    service = _service(
        monkeypatch,
        [
            ReasoningUnavailableError(
                "Synthetic provider outage."
            ),
        ],
    )

    response = await service.generate_reasoning(
        _request()
    )

    assert service.provider.call_count == 1

    assert response.candidate_reasoning == []

    assert (
        "provider is unavailable"
        in response.reasoning_summary.lower()
    )


@pytest.mark.asyncio
async def test_retry_preserves_same_original_context(
    monkeypatch,
):
    unsafe = _json_response(
        summary=(
            "This confirms the diagnosis of Pneumonia."
        )
    )

    service = _service(
        monkeypatch,
        [
            unsafe,
            _json_response(),
        ],
    )

    response = await service.generate_reasoning(
        _request()
    )

    assert service.provider.call_count == 2

    assert response.requires_doctor_review is True

    first_prompt = service.provider.prompts[0]
    retry_prompt = service.provider.prompts[1]

    assert "Pneumonia" in first_prompt
    assert "Pneumonia" in retry_prompt

    assert first_prompt in retry_prompt
