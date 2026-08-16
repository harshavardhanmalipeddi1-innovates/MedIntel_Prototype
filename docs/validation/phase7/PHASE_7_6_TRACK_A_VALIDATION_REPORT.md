# MedIntel Phase 7 Track A Validation Report

## 1. Validation Identity

Validation run: track-a-20260810-151708

Frozen Phase 7.5 documentation commit:

863d1391aefbd6936e7026130df05585e5e77989

System under evaluation:

MedIntel respiratory clinical decision-support research prototype.

Dataset:

Reconstructed official-release DDXPlus synthetic respiratory Track A benchmark.

This report describes retrospective synthetic technical validation.
It is not clinical validation.

## 2. Track A Cohort

- Strict respiratory test cases: 46,334
- Frozen respiratory disease classes: 13
- Reference: DDXPlus synthetic PATHOLOGY label
- No post-result relabeling
- No retraining
- No threshold tuning

## 3. Phase 7.5A — Primary Ranking

Status: PASS

- Top-1 accuracy: 0.99954676911123586
- Top-3 inclusion: 1
- Top-5 inclusion: 1
- Macro Top-1: 0.99976212514892349
- Correct Top-1 cases: 46,313
- Top-1 errors: 21

All 21 Top-1 errors were confined to:

- Viral pharyngitis -> Acute laryngitis: 18
- Acute laryngitis -> Viral pharyngitis: 3

## 4. Phase 7.5B — Partial-History Robustness

Status: PASS

- Full-history Top-1: 0.9995467691
- 75% evidence mean Top-1: 0.99624465835
- 50% evidence mean Top-1: 0.98733111754
- 25% evidence mean Top-1: 0.93943972029
- Initial-evidence-only Top-1: 0.35446971986
- Initial-evidence-only Top-3: 0.66981050632
- Initial-evidence-only Top-5: 0.8380023309

The decline under reduced evidence is reported descriptively and is not
converted into a clinical acceptance threshold.

## 5. Phase 7.5C — Differential Analysis

Status: PASS

- Closed-world mass capture@5: 0.72273862361907959
- Closed-world label recall@5: 0.68933936591650147
- NDCG@5: 0.80101041677900719
- LRAP: 0.81455117464065552
- Top-1 agreement: 0.65975309707773988
- Full official DDx mass capture@5: 0.42193122295182445
- Full official DDx label recall@5: 0.33310262176273714

Historical missing differential regressors were not reconstructed.
The scope model was not used as a disease ranker.

## 6. Phase 7.5D — Critical Conditions

Status: PASS

Critical conditions:

- bronchospasm / acute asthma exacerbation
- pneumonia
- pulmonary embolism
- spontaneous pneumothorax
- tuberculosis

Reference cases: 12604

Full-history:

- Top-1: 1
- Top-3: 1
- Top-5: 1
- failures: 0

## 7. Phase 7.5E — Candidate Yield

Status: PASS

- Evaluated cases: 46334
- Zero candidates: 0
- One candidate: 46247
- Two candidates: 87
- Mean candidate count: 1.0018776708248802
- At least one candidate: 100%
- Reference inclusion Top-1: 0.9995467691
- Reference inclusion Top-3: 0.9999784176
- Reference inclusion Top-5/all returned: 0.9999784176

One frozen case had the reference diagnosis absent from the
threshold-constrained returned candidate set and is classified in
failure_cases.csv as candidate truncation.

## 8. Exploratory Subgroup Reporting

Machine-readable output:

outputs/subgroup_metrics.csv

Reported dimensions:

- disease
- sex
- evidence-completeness condition

Age subgroup performance was not computed because no frozen Track A
age-band cut-points were available in the locked reporting specification.
No post-result age bands were invented.

Subgroup results are exploratory, not confirmatory clinical claims.

## 9. Failure Analysis

Machine-readable output:

outputs/failure_cases.csv

Frozen failure categories observed:

- primary ranking miss: 21 cases
- candidate truncation: 1 case

A case may carry more than one category, so category counts must not be
blindly summed as unique-patient counts.

Failure analysis was performed after the system was frozen and was not
used to tune the evaluated implementation.

## 10. Phase 7.5F — Structural Safety

Status: INCOMPLETE_TIME_LIMIT

- Locked live cohort: 151 cases
- Pre-execution identity verification: 151/151 PASS
- Deterministic safety control scenarios: 10/10 PASS
- Completed live MedGemma cases: 2/151
- Final safety_metrics.json: NOT PRODUCED
- Final Gate A5: NOT ASSESSED

The live MedGemma evaluation was terminated because of available
execution-time constraints.

This is neither an A5 safety pass nor an A5 safety failure.

The 10/10 deterministic control-scenario result must not be substituted
for completion of the locked 151-case live safety cohort.

## 11. Technical Gate Status

- Gate A1 — source and cohort identity: PASS
- Gate A2 — frozen artifact identity: PASS
- Gate A3 — metric/output completeness: INCOMPLETE
- Gate A4 — robustness protocol completion: PASS
- Gate A5 — deterministic workflow safety: NOT ASSESSED
- Gate A6 — no-tuning compliance: PASS

Gate A3 is not represented as fully satisfied because the locked live
safety evaluation did not complete and final safety_metrics.json was not
produced.

The overall Track A evaluation therefore must not be described as
passing all frozen technical gates.

## 12. Protocol Deviations and Limitations

Existing protocol-deviation record:

outputs/protocol_deviations.md

SHA256:

$ProtocolHash

Important limitations include:

1. Phase 7.5F-v1 was invalidated before live measurement after a
   formally demonstrated validation-harness ordering defect.
2. Corrected Phase 7.5F-v2 passed locked pre-execution identity checks.
3. The v2 live cohort was intentionally stopped after 2/151 cases
   because of available execution-time constraints.
4. Final safety_metrics.json therefore does not exist.
5. No final A5 result is assigned.
6. Age subgroup metrics were not generated because no frozen age-band
   cut-points were available; no post-result age bins were created.
7. Track A uses synthetic DDXPlus benchmark labels rather than
   clinician-adjudicated real-world diagnoses.

## 13. Interpretation Boundary

Supported conclusion:

Phase 7.5A through Phase 7.5E produced retrospective synthetic technical
validation evidence for the frozen MedIntel respiratory research
prototype.

Not supported:

- clinical validation
- proven diagnostic performance in real patients
- autonomous diagnosis
- autonomous prescription
- unsupervised clinical use
- regulatory approval
- production-readiness claims

The treating doctor remains the final clinical decision-maker.

## 14. Reporting Artifact Integrity

subgroup_metrics.csv SHA256:

$SubgroupHashPre

failure_cases.csv SHA256:

$FailureHashPre

The external validation run directory remains outside the MedIntel
source-code repository.
