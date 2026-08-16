import pytest
from backend.app.modules.reasoning_engine.context_builder import ContextBuilder
from backend.app.modules.reasoning_engine.prompt_builder import PromptBuilder
from backend.app.modules.reasoning_engine.response_parser import ResponseParser
from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ReasoningDifferentialItem,
    ClinicalRuleResult
)
import json

@pytest.fixture
def sample_request():
    return ClinicalReasoningRequest(
        patient_context={"age": 45, "symptoms": ["cough"]},
        rules=ClinicalRuleResult(alerts=["Check for pneumonia"], status="evaluated"),
        differential=[
            ReasoningDifferentialItem(
                rank=1,
                disease="Pneumonia",
                probability=0.85,
                confidence="High"
            )
        ]
    )

def test_context_builder(sample_request):
    context_str = ContextBuilder.build_context(sample_request)
    data = json.loads(context_str)
    assert data["Patient_Context"]["age"] == 45
    assert len(data["Ranked_Differential_Candidates"]) == 1
    assert data["Ranked_Differential_Candidates"][0]["Disease"] == "Pneumonia"

def test_prompt_builder(sample_request):
    context_str = ContextBuilder.build_context(sample_request)
    prompt = PromptBuilder.build_prompt(context_str)
    assert "Pneumonia" in prompt
    assert "You are NOT the final diagnostic authority" in prompt

def test_response_parser_valid():
    raw = '```json\n{"candidate_reasoning": []}\n```'
    parsed = ResponseParser.parse(raw)
    assert isinstance(parsed, dict)
    assert "candidate_reasoning" in parsed

def test_response_parser_invalid():
    with pytest.raises(ValueError):
        ResponseParser.parse("This is not JSON")

def test_response_parser_medgemma_thought_then_json():
    raw = '''thought
The model produced internal reasoning that must never be exposed.

```json
{"candidate_reasoning": [], "reasoning_summary": "Final structured result.", "requires_doctor_review": true}
```'''

    parsed = ResponseParser.parse(raw)

    assert parsed["reasoning_summary"] == "Final structured result."
    assert parsed["requires_doctor_review"] is True
    assert "thought" not in json.dumps(parsed).lower()


def test_response_parser_uses_final_valid_json_object():
    raw = '''thought
Internal reasoning.

{"status": "intermediate"}

More model text.

{"status": "final"}'''

    parsed = ResponseParser.parse(raw)

    assert parsed == {"status": "final"}



def test_prompt_builder_contains_non_authoritative_guardrails(
    sample_request,
):
    context_str = ContextBuilder.build_context(sample_request)
    prompt = PromptBuilder.build_prompt(context_str)

    assert "most likely diagnosis" in prompt
    assert "findings support consideration of this candidate" in prompt
    assert "must not be reinterpreted as diagnostic certainty" in prompt


def test_context_builder_adds_semantic_initial_evidence(sample_request):
    request = sample_request.model_copy(
        update={
            "patient_context": {
                "age": 58,
                "sex": "M",
                "initial_evidence": "E_77",
                "positive_evidence_tokens": ["E_66"],
                "answered_question_codes": ["E_66"],
                "evidence_tokens": [
                    "E_66",
                    "INITIAL::E_77",
                ],
            }
        }
    )

    context_str = ContextBuilder.build_context(request)
    data = json.loads(context_str)

    semantic = data["Semantic_Evidence_Context"]
    observed = semantic["Observed_Clinical_Evidence"]

    initial = next(
        item
        for item in observed
        if item["Code"] == "E_77"
    )

    assert initial["Source"] == "initial_evidence"
    assert initial["Observed"] is True
    assert initial["Initial_Evidence"] is True

    assert (
        initial["Clinical_Meaning"]
        == "Do you have a cough that produces colored or more abundant sputum than usual?"
    )

    assert (
        data["Patient_Context"]["evidence_tokens"]
        == ["E_66", "INITIAL::E_77"]
    )


def test_context_builder_semanticizes_positive_evidence(sample_request):
    request = sample_request.model_copy(
        update={
            "patient_context": {
                "initial_evidence": "E_77",
                "positive_evidence_tokens": ["E_66"],
                "answered_question_codes": ["E_66"],
                "evidence_tokens": [
                    "E_66",
                    "INITIAL::E_77",
                ],
            }
        }
    )

    data = json.loads(
        ContextBuilder.build_context(request)
    )

    observed = data[
        "Semantic_Evidence_Context"
    ]["Observed_Clinical_Evidence"]

    finding = next(
        item
        for item in observed
        if item["Code"] == "E_66"
    )

    assert finding["Original_Token"] == "E_66"
    assert finding["Observed"] is True
    assert finding["Clinical_Meaning"]
    assert finding["Clinical_Meaning"] != "E_66"


def test_context_builder_decodes_value_bearing_token():
    code, value, initial = ContextBuilder._decode_evidence_token(
        "E_130_@_V_11"
    )

    assert code == "E_130"
    assert value == "V_11"
    assert initial is False


def test_prompt_builder_contains_evidence_semantic_guardrails(
    sample_request,
):
    context_str = ContextBuilder.build_context(sample_request)
    prompt = PromptBuilder.build_prompt(context_str)

    assert "EVIDENCE SEMANTIC RULES:" in prompt
    assert "Initial evidence is already observed patient evidence" in prompt
    assert "Observed_Clinical_Evidence" in prompt
    assert "Explicitly_Answered_Question_Codes" in prompt
