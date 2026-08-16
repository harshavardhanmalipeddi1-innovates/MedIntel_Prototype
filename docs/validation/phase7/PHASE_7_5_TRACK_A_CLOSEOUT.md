# Phase 7.5 Track A — Validation Closeout

Validation run: track-a-20260810-151708

## Scope

Retrospective technical validation of the frozen MedIntel respiratory
clinical decision-support research prototype using the synthetic DDXPlus
respiratory validation cohort.

This is not clinical validation.

## Phase 7.5A — Primary Ranking

Status: PASS

- Strict respiratory cohort: 46,334 cases
- Respiratory classes: 13
- Top-1 accuracy: 0.9995467691
- Top-3 accuracy: 1.0000000000
- Top-5 accuracy: 1.0000000000
- Macro Top-1: 0.9997621251
- Top-1 errors: 21

## Phase 7.5B — Partial-History Robustness

Status: PASS

- Full-history Top-1: 0.9995467691
- 75% evidence retention mean Top-1: 0.9962446584
- 50% evidence retention mean Top-1: 0.9873311175
- 25% evidence retention mean Top-1: 0.9394397203
- Initial-evidence-only Top-1: 0.3544697199
- Initial-evidence-only Top-3: 0.6698105063
- Initial-evidence-only Top-5: 0.8380023309

## Phase 7.5C — Differential Analysis

Status: PASS

- Closed-world probability-mass capture@5: 0.7227386236
- Closed-world label recall@5: 0.6893393659
- NDCG@5: 0.8010104168
- LRAP: 0.8145511746
- Top-1 agreement: 0.6597530971
- Full official DDx mass capture@5: 0.4219312230
- Full official DDx label recall@5: 0.3331026218
- Supported-scope mass ceiling: 0.6002981886
- Supported-scope label ceiling: 0.4973185243

## Phase 7.5D — Critical-Condition Reporting

Status: PASS

- Critical conditions: 5
- Reference cases: 12,604
- Full-history Top-1: 1.0
- Full-history Top-3: 1.0
- Full-history Top-5: 1.0
- Full-history failures: 0

## Phase 7.5E — Candidate Yield

Status: PASS

- Evaluated cases: 46,334
- Zero-candidate cases: 0
- One-candidate cases: 46,247
- Two-candidate cases: 87
- At least one candidate: 100%
- Mean candidate count: 1.0018776708
- Reference inclusion Top-1: 0.9995467691
- Reference inclusion Top-3: 0.9999784176
- Reference inclusion Top-5: 0.9999784176

## Phase 7.5F — Structural Safety

Status: INCOMPLETE — EXECUTION-TIME LIMIT

- Evaluator: Phase 7.5F-v2
- Locked-case identity: 151/151 PASS
- Deterministic safety controls: 10/10 PASS
- Locked live cohort: 151 cases
- Completed live cases: 2
- Final A5 structural-safety gate: NOT ASSESSED

The live MedGemma cohort was intentionally terminated because of the
available project execution-time constraint.

This Phase 7.5F result is neither a safety pass nor a safety failure.

## Final Track-A Interpretation

Phase 7.5A through Phase 7.5E completed successfully under the locked
retrospective technical-validation protocol.

Phase 7.5F verified all 151 locked case identities and passed all 10
deterministic safety-control scenarios, but the full live reasoning
cohort was not completed.

Therefore:

- retrospective technical-validation evidence is available;
- final live structural-safety A5 evidence remains incomplete;
- clinical validation has not been performed;
- no autonomous diagnosis claim is supported;
- no autonomous prescription claim is supported;
- the doctor remains the final clinical decision-maker.
