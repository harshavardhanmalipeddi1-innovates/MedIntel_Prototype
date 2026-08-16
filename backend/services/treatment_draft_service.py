from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
)
from backend.app.schemas.treatment_schema import (
    TreatmentConsideration,
    TreatmentDraftResponse,
)


class TreatmentDraftService:
    """
    Builds a clinician-review treatment consideration draft.

    This phase does not generate prescriptions, medication orders,
    doses, or autonomous treatment decisions.

    Until MedIntel has a validated structured treatment knowledge source,
    this service only identifies candidate-specific review considerations,
    known KB cautions, and missing information.
    """

    def generate_draft(
        self,
        request: ClinicalReasoningRequest,
        reasoning: ClinicalReasoningResponse,
    ) -> TreatmentDraftResponse:

        considerations = []
        general_cautions = [
            "AI-generated clinical support draft. Not a prescription.",
            "Treatment decisions require clinician review and approval.",
        ]

        reasoning_by_candidate = {
            item.disease.lower(): item
            for item in reasoning.candidate_reasoning
        }

        for candidate in request.differential:
            knowledge = candidate.knowledge
            candidate_reasoning = reasoning_by_candidate.get(
                candidate.disease.lower()
            )

            warnings = []
            missing_information = []

            if knowledge is None:
                warnings.append(
                    "No structured disease knowledge is available for this candidate."
                )
            else:
                # These are disease-level KB cautions only.
                # They are NOT assumed to apply to this patient.
                warnings.extend(
                    f"Knowledge-base caution requiring clinician review: {item}"
                    for item in knowledge.contraindications
                )

                warnings.extend(
                    (
                        f"Knowledge-base red-flag screening item; "
                        f"check for: {item}. "
                        "This does not establish that the finding is "
                        "present in this patient."
                    )
                    for item in knowledge.red_flags
                )

            if candidate_reasoning is not None:
                missing_information.extend(
                    candidate_reasoning.missing_information
                )

            missing_information.extend(
                reasoning.important_uncertainties
            )
            missing_information.extend(
                reasoning.next_information_needed
            )

            missing_information = sorted(set(missing_information))

            considerations.append(
                TreatmentConsideration(
                    candidate_disease=candidate.disease,
                    consideration=(
                        "Review appropriate management options for this "
                        "existing differential candidate using validated "
                        "clinical guidance and patient-specific information."
                    ),
                    rationale=(
                        "Candidate preserved from the existing MedIntel "
                        "differential. No autonomous treatment recommendation "
                        "or prescription has been generated."
                    ),
                    warnings=warnings,
                    missing_information=missing_information,
                    contraindication_concern=bool(
                        knowledge and knowledge.contraindications
                    ),
                )
            )

        return TreatmentDraftResponse(
            considerations=considerations,
            general_cautions=general_cautions,
            status="AI_GENERATED_DRAFT",
            requires_doctor_review=True,
            doctor_approval_status="PENDING",
        )
