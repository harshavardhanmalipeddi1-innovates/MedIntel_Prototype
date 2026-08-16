from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.knowledge_schema import DiseaseKnowledge


class StrictSchema(BaseModel):
    """Base schema that rejects unexpected fields."""

    model_config = ConfigDict(extra="forbid")


class ClinicalRuleResult(StrictSchema):
    """Clinical rule-engine output passed to the reasoning layer."""

    alerts: List[str] = Field(default_factory=list)
    status: str = "evaluated"


class ReasoningDifferentialItem(StrictSchema):
    """
    One ranked disease candidate produced by the existing
    Differential Diagnosis Manager.

    Rank and probability originate from the ML pipeline and must
    not be modified by the reasoning model.
    """

    rank: int = Field(ge=1)
    disease: str = Field(min_length=1)
    probability: float = Field(ge=0.0, le=1.0)
    confidence: str
    knowledge: Optional[DiseaseKnowledge] = None


class ClinicalReasoningRequest(StrictSchema):
    """
    Structured input to Phase 3.8.

    patient_context:
        Original clinician-supplied clinical information.

    rules:
        Existing ClinicalRules output.

    differential:
        Ranked candidates produced by XGBoost + differential manager.
    """

    patient_context: Dict[str, Any]
    rules: ClinicalRuleResult = Field(default_factory=ClinicalRuleResult)
    differential: List[ReasoningDifferentialItem] = Field(
        min_length=1,
        max_length=5,
    )


class CandidateReasoning(StrictSchema):
    """
    Concise reasoning for one existing differential candidate.

    This schema intentionally contains no diagnosis-finalization
    or treatment/prescription fields.
    """

    rank: int = Field(ge=1)
    disease: str = Field(min_length=1)

    supporting_findings: List[str] = Field(default_factory=list)
    conflicting_findings: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)

    rationale: str = Field(min_length=1)


class ClinicalReasoningResponse(StrictSchema):
    """
    Validated clinical reasoning output.

    The treating clinician always remains responsible for the
    final diagnosis and treatment decision.
    """

    candidate_reasoning: List[CandidateReasoning] = Field(default_factory=list)

    important_uncertainties: List[str] = Field(default_factory=list)
    red_flags_to_review: List[str] = Field(default_factory=list)
    next_information_needed: List[str] = Field(default_factory=list)

    reasoning_summary: str = Field(min_length=1)
    limitations: List[str] = Field(default_factory=list)

    requires_doctor_review: Literal[True] = True
