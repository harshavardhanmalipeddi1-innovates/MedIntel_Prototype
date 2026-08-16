import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.services.assessment_service import AssessmentService


client = TestClient(app)


def _service():
    return AssessmentService()


def _valid_initial(service):
    return sorted(service._initial_evidence_codes())[0]


def _noninitial_binary(service, initial):
    encoder = service._encoder_class_set()

    for code in service._base_codes():
        if code == initial:
            continue

        details = service._evidence_details(code)

        if (
            details.get("data_type") == "B"
            and code in encoder
        ):
            return code

    raise AssertionError("No model-supported binary evidence found.")


def test_questionnaire_contract_remains_stable():
    service = _service()
    questionnaire = service.get_questionnaire()

    assert questionnaire["question_count"] == 85
    assert questionnaire["initial_evidence_count"] == 25


def test_initial_only_context_uses_initial_marker():
    service = _service()
    initial = _valid_initial(service)

    result = service.prepare_assessment(
        age=45,
        sex="M",
        initial_evidence=initial,
        answers=[],
    )

    context = result["patient_context"]

    assert context["evidence_tokens"] == [f"INITIAL::{initial}"]
    assert context["NONINITIAL_EVIDENCE_COUNT"] == 0
    assert context["INITIAL_EVIDENCE_ONLY"] == 1.0
    assert context["QUESTIONNAIRE_COMPLETION_FRACTION"] == 0.0
    assert context["CONSULTATION_STAGE_CODE"] == 0.0
    assert result["eligible_question_count"] == 84


def test_binary_positive_creates_noninitial_token():
    service = _service()
    initial = _valid_initial(service)
    code = _noninitial_binary(service, initial)

    result = service.prepare_assessment(
        age=45,
        sex="F",
        initial_evidence=initial,
        answers=[{"code": code, "value": True}],
    )

    context = result["patient_context"]

    assert code in result["positive_evidence_tokens"]
    assert context["NONINITIAL_EVIDENCE_COUNT"] == 1
    assert context["INITIAL_EVIDENCE_ONLY"] == 0.0
    assert context["SEX_MALE_CODE"] == 0.0


def test_binary_negative_counts_as_answer_but_not_positive():
    service = _service()
    initial = _valid_initial(service)
    code = _noninitial_binary(service, initial)

    result = service.prepare_assessment(
        age=45,
        sex="M",
        initial_evidence=initial,
        answers=[{"code": code, "value": False}],
    )

    assert code in result["answered_question_codes"]
    assert code not in result["positive_evidence_tokens"]
    assert result["patient_context"]["NONINITIAL_EVIDENCE_COUNT"] == 0
    assert result["answered_question_count"] == 1
    assert result["questionnaire_completion_fraction"] == pytest.approx(
        1 / 84
    )


def test_invalid_initial_evidence_is_rejected():
    service = _service()

    with pytest.raises(ValueError, match="not a valid initial"):
        service.prepare_assessment(
            age=45,
            sex="M",
            initial_evidence="E_NOT_REAL",
            answers=[],
        )


def test_duplicate_answer_is_rejected():
    service = _service()
    initial = _valid_initial(service)
    code = _noninitial_binary(service, initial)

    with pytest.raises(ValueError, match="Duplicate answer"):
        service.prepare_assessment(
            age=45,
            sex="M",
            initial_evidence=initial,
            answers=[
                {"code": code, "value": True},
                {"code": code, "value": False},
            ],
        )


def test_feature_vector_is_built_from_prepared_context():
    service = _service()
    initial = _valid_initial(service)

    result = service.prepare_assessment(
        age=45,
        sex="M",
        initial_evidence=initial,
        answers=[],
    )

    matrix = service._feature_builder.build_feature_vector(
        result["patient_context"]
    )

    assert matrix.shape[0] == 1
    assert matrix.shape[1] == len(
        service._feature_builder.get_feature_names()
    )


def test_prepare_endpoint_returns_model_context(authenticated_client):
    service = _service()
    initial = _valid_initial(service)

    response = authenticated_client.post(
        "/api/v1/clinical/assessment/prepare",
        json={
            "age": 45,
            "sex": "M",
            "initial_evidence": initial,
            "answers": [],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["initial_evidence"] == initial
    assert data["patient_context"]["evidence_tokens"] == [
        f"INITIAL::{initial}"
    ]
    assert data["eligible_question_count"] == 84


def test_prepare_endpoint_rejects_invalid_initial(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/clinical/assessment/prepare",
        json={
            "age": 45,
            "sex": "M",
            "initial_evidence": "E_NOT_REAL",
            "answers": [],
        },
    )

    assert response.status_code == 400
