from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssessmentOption(StrictSchema):
    value: str
    label: str


class AssessmentQuestion(StrictSchema):
    code: str
    question: str
    data_type: str
    answer_kind: str
    is_antecedent: bool = False
    initial_evidence_allowed: bool = False
    default_value: Any = None
    options: list[AssessmentOption] = Field(default_factory=list)
    scale_min: int | None = None
    scale_max: int | None = None


class AssessmentQuestionnaireResponse(StrictSchema):
    version: str
    question_count: int
    initial_evidence_count: int
    initial_evidence_codes: list[str] = Field(default_factory=list)
    questions: list[AssessmentQuestion] = Field(default_factory=list)
    source: dict[str, Any] = Field(default_factory=dict)


class AssessmentAnswer(StrictSchema):
    code: str
    value: Any


class AssessmentPrepareRequest(StrictSchema):
    age: int = Field(ge=0, le=120)
    sex: Literal["M", "F"]
    initial_evidence: str
    answers: list[AssessmentAnswer] = Field(default_factory=list)


class AssessmentPrepareResponse(StrictSchema):
    patient_context: dict[str, Any]
    initial_evidence: str
    positive_evidence_tokens: list[str] = Field(default_factory=list)
    answered_question_codes: list[str] = Field(default_factory=list)
    eligible_question_codes: list[str] = Field(default_factory=list)
    answered_question_count: int
    eligible_question_count: int
    questionnaire_completion_fraction: float
