import pytest

from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
)
from backend.services.reasoning_provider import ReasoningProvider


class FakeReasoningProvider(ReasoningProvider):
    async def generate_reasoning(
        self,
        request: ClinicalReasoningRequest,
    ) -> ClinicalReasoningResponse:
        return ClinicalReasoningResponse(
            candidate_reasoning=[],
            important_uncertainties=[],
            red_flags_to_review=[],
            next_information_needed=[],
            reasoning_summary="Mock reasoning response.",
            limitations=["Test provider only."],
            requires_doctor_review=True,
        )


def test_reasoning_provider_is_abstract():
    with pytest.raises(TypeError):
        ReasoningProvider()


@pytest.mark.asyncio
async def test_fake_reasoning_provider_implements_interface():
    provider = FakeReasoningProvider()

    request = ClinicalReasoningRequest(
        patient_context={"cough": True},
        differential=[
            {
                "rank": 1,
                "disease": "Pneumonia",
                "probability": 0.82,
                "confidence": "medium",
                "knowledge": None,
            }
        ],
    )

    response = await provider.generate_reasoning(request)

    assert response.requires_doctor_review is True
    assert response.reasoning_summary == "Mock reasoning response."

def test_reasoning_service_rejects_unknown_provider(monkeypatch):
    import pytest

    from backend.app.config.settings import settings
    from backend.services.reasoning_service import ReasoningService

    monkeypatch.setattr(settings, "AI_PROVIDER", "invalid-provider")

    with pytest.raises(ValueError, match="Unsupported AI_PROVIDER"):
        ReasoningService()



@pytest.mark.asyncio
async def test_reasoning_service_classifies_schema_validation(
    monkeypatch,
):
    from backend.app.config.settings import settings
    from backend.services.reasoning_service import ReasoningService

    monkeypatch.setattr(settings, "AI_PROVIDER", "local")
    monkeypatch.setattr(settings, "AI_REASONING_ENABLED", True)

    service = ReasoningService()

    async def invalid_schema_response(_prompt: str) -> str:
        return (
            '{"candidate_reasoning": [], '
            '"reasoning_summary": "Schema test", '
            '"requires_doctor_review": true, '
            '"unexpected_field": "rejected"}'
        )

    monkeypatch.setattr(
        service.provider,
        "generate_reasoning",
        invalid_schema_response,
    )

    request = ClinicalReasoningRequest(
        patient_context={"test_case": True},
        differential=[
            {
                "rank": 1,
                "disease": "Pneumonia",
                "probability": 0.82,
                "confidence": "High",
                "knowledge": None,
            }
        ],
    )

    response = await service.generate_reasoning(request)

    assert "schema validation" in response.reasoning_summary.lower()
