from backend.app.schemas.reasoning_schema import (
    ClinicalReasoningRequest,
    ClinicalReasoningResponse,
)
from backend.app.schemas.verification_schema import (
    ClinicalVerificationResponse,
    VerificationStep,
)


class VerificationService:
    """
    Generates clinician-review verification suggestions from deterministic
    Clinical Rules, Knowledge Base data, and validated AI reasoning.

    This service does not autonomously order investigations.
    """

    @staticmethod
    def _categorize_investigation(investigation: str) -> str:
        text = investigation.lower()

        if any(term in text for term in ("blood", "culture", "cbc", "laboratory", "lab")):
            return "laboratory"

        if any(term in text for term in ("x-ray", "xray", "scan", "ct", "mri", "ultrasound")):
            return "imaging"

        return "other"

    def generate_verification_plan(
        self,
        request: ClinicalReasoningRequest,
        reasoning: ClinicalReasoningResponse,
    ) -> ClinicalVerificationResponse:

        steps = []
        missing_info = set()

        # 1. Deterministic Clinical Rules safety alerts.
        for alert in request.rules.alerts:
            steps.append(
                VerificationStep(
                    candidate_disease="General Clinical Safety",
                    reason="Clinical rule safety alert",
                    priority="high",
                    category="other",
                    supporting_context=alert,
                    is_red_flag=True,
                )
            )

        # 2. Deterministic Knowledge Base guidance.
        for candidate in request.differential:
            knowledge = candidate.knowledge

            if knowledge is None:
                continue

            # Knowledge-base red flags are disease-level screening guidance.
            # They do NOT establish that the finding is present in this patient.
            # Critical/PRESENT semantics require deterministic patient evidence.
            # No fuzzy text matching is performed here.
            for red_flag in knowledge.red_flags:
                steps.append(
                    VerificationStep(
                        candidate_disease=candidate.disease,
                        reason=(
                            f"Screen/check knowledge-base red flag for "
                            f"{candidate.disease}"
                        ),
                        priority="high",
                        category="other",
                        supporting_context=(
                            f"Screen/check for: {red_flag}. "
                            "Knowledge-base guidance only; this does not "
                            "establish that the finding is present in this patient."
                        ),
                        is_red_flag=False,
                    )
                )

            for examination in knowledge.physical_examination:
                steps.append(
                    VerificationStep(
                        candidate_disease=candidate.disease,
                        reason="Knowledge-base physical examination consideration",
                        priority="medium",
                        category="physical_examination",
                        supporting_context=examination,
                        is_red_flag=False,
                    )
                )

            for investigation in knowledge.recommended_investigations:
                steps.append(
                    VerificationStep(
                        candidate_disease=candidate.disease,
                        reason="Knowledge-base investigation consideration",
                        priority="medium",
                        category=self._categorize_investigation(investigation),
                        supporting_context=investigation,
                        is_red_flag=False,
                    )
                )

        # 3. Validated reasoning may identify information that needs review.
        for candidate_reasoning in reasoning.candidate_reasoning:
            missing_info.update(candidate_reasoning.missing_information)

        missing_info.update(reasoning.important_uncertainties)
        missing_info.update(reasoning.next_information_needed)

        # AI-highlighted concerns remain clinician-review suggestions.
        # They are NOT promoted to deterministic critical red flags.
        for concern in reasoning.red_flags_to_review:
            steps.append(
                VerificationStep(
                    candidate_disease="AI Highlighted",
                    reason="AI-highlighted concern requiring clinician verification",
                    priority="high",
                    category="other",
                    supporting_context=concern,
                    is_red_flag=False,
                )
            )

        return ClinicalVerificationResponse(
            suggested_steps=steps,
            missing_information_summary=sorted(missing_info),
            requires_doctor_review=True,
        )
