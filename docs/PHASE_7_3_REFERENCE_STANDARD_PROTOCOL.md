# MedIntel Phase 7.3 — Reference Standard and Ground-Truth Adjudication Protocol

## 1. Status

**Protocol stage:** REFERENCE STANDARD AND GROUND-TRUTH DEFINITION

**System under evaluation:** Frozen MedIntel respiratory clinical
decision-support research prototype.

**Phase 6 frozen implementation commit:**

`388d847bdd7a9f3377c77beb019eac242ffc43c1`

**Phase 7.1 validation protocol commit:**

`527400e3970385f8b4f9c1f2b14a6eed44099997`

**Phase 7.2 dataset-provenance commit:**

`84ab20dc305c46e465dd230040ecca91fd7a4c14`

The prototype remains **not clinically validated**.

Phase 7.3 defines how reference labels and clinical ground truth must be
established before clinical-performance claims may be considered.

It does not change the frozen model, preprocessing, prompts, knowledge base,
SafetyValidator rules, or workflow behavior.

---

## 2. Validation Tracks

Phase 7 uses separate evidence tracks.

### Track A — Synthetic DDXPlus benchmark

Track A evaluates algorithmic behavior using the reconstructed official
DDXPlus synthetic case set.

Track A is research benchmarking only.

It is not clinical validation.

### Track B — Governed real-world clinical evaluation

Track B is reserved for a future governed external clinical dataset.

Track B requires a prospectively defined clinical reference-standard
procedure independent of MedIntel outputs.

### Track C — Clinician review / human-factors assessment

Track C evaluates clinician review, interpretability, workflow usefulness,
and safety perception.

Track C must not substitute for diagnostic-performance validation.

---

## 3. Track A Reference Standard

For Track A, the primary reference label is the official DDXPlus:

`PATHOLOGY`

field associated with each synthetic patient record.

The DDXPlus `PATHOLOGY` label is treated as the benchmark-generating
reference label for synthetic evaluation.

It must not be described as:

- clinician-adjudicated diagnosis,
- chart-confirmed diagnosis,
- pathology-confirmed diagnosis,
- real-world clinical ground truth,
- prospective diagnostic truth.

The correct interpretation is:

**synthetic benchmark reference label**

Track A therefore measures agreement with the DDXPlus synthetic benchmark,
not agreement with independently established real-world clinical truth.

---

## 4. Locked Track A Case Set

The official English DDXPlus release was reacquired and its source identity
verified before reconstruction.

Historical split and overlap rules were reproduced exactly.

The locked Track A respiratory cohorts are:

- strict respiratory validation: **46,125**
- strict respiratory test: **46,334**
- frozen respiratory disease classes: **13**

The reconstructed test cohort reproduces the historical case ordering for
all 46,334 cases using:

- test row,
- age,
- sex,
- ground-truth pathology.

Track A evaluation must use this reconstructed strict cohort.

A new random split must not replace it.

Records must not be sampled, padded, duplicated, deleted, or reordered for
the purpose of improving reported performance.

---

## 5. Frozen Track A Disease Scope

The closed-world Track A disease-ranking scope contains exactly:

1. Acute COPD exacerbation / infection
2. Acute laryngitis
3. Bronchiectasis
4. Bronchitis
5. Bronchospasm / acute asthma exacerbation
6. Influenza
7. Pneumonia
8. Pulmonary embolism
9. Pulmonary neoplasm
10. Spontaneous pneumothorax
11. Tuberculosis
12. URTI
13. Viral pharyngitis

Performance within this 13-condition benchmark must not be represented as
performance across all respiratory disease.

---

## 6. Track A Differential-Diagnosis Information

DDXPlus also contains:

`DIFFERENTIAL_DIAGNOSIS`

information.

This may be used only for separately specified secondary research analyses.

It must not silently replace `PATHOLOGY` as the primary Track A reference
label for disease-ranking performance.

Any metric based on the provided differential diagnosis must be labeled
explicitly as a differential-list or differential-relevance analysis.

---

## 7. Track A Reference-Label Integrity

No Track A reference label may be altered after evaluation begins.

The evaluator must not:

- relabel errors based on model output,
- remove difficult cases after reviewing errors,
- merge diseases after seeing performance,
- modify thresholds to improve the frozen test result,
- reinterpret unsupported cases as correct predictions,
- use MedIntel reasoning output to alter benchmark truth.

Disagreements between MedIntel and DDXPlus remain evaluation errors or
analysis cases unless a pre-specified data-integrity defect is independently
demonstrated.

---

## 8. Track B Clinical Reference Standard

A future real-world Track B study requires a reference standard independent
of MedIntel predictions.

The reference standard must be derived from governed clinical source data
that may include, where available:

- documented clinical history,
- physical examination,
- laboratory findings,
- imaging,
- microbiology,
- pulmonary testing,
- specialist assessment,
- discharge diagnosis,
- follow-up information,
- clinically relevant outcomes.

No single data field should automatically be assumed to constitute clinical
truth unless the Track B study protocol prospectively defines and justifies
it.

---

## 9. Blinding Requirement

Clinicians establishing or adjudicating Track B reference labels must not
use MedIntel's prediction, candidate ranking, MedGemma reasoning, treatment
draft, or confidence values to establish the reference diagnosis.

Reference-standard creation and MedIntel evaluation must remain logically
separated.

Where technically feasible, adjudicators should be blinded to all MedIntel
outputs until the reference label is locked.

---

## 10. Independent Clinical Review

For a future Track B dataset, each included case should undergo independent
clinical review by at least two appropriately qualified clinicians.

Each reviewer should assign, according to the Track B protocol:

- primary reference diagnosis,
- relevant alternative diagnoses where appropriate,
- whether the case is within the frozen MedIntel respiratory scope,
- whether sufficient information exists for adjudication,
- clinically important red-flag findings where relevant,
- confidence in the assigned reference standard.

Reviewer identities and qualifications must be recorded in the governed
study records.

Patient-identifying information must not be committed to the MedIntel Git
repository.

---

## 11. Disagreement Adjudication

If independent Track B reviewers disagree on the primary reference
diagnosis, the disagreement must not be resolved by MedIntel.

A separate adjudication process must be used.

The preferred procedure is:

1. retain both independent initial judgments,
2. record the nature of the disagreement,
3. obtain review from an independent adjudicating clinician,
4. permit review of the governed clinical source record,
5. lock the final adjudicated reference label,
6. preserve the original reviewer labels for agreement analysis.

The adjudicator must not use MedIntel output to determine the final label.

---

## 12. Uncertain and Non-Adjudicable Cases

Real clinical records may not support a defensible single reference
diagnosis.

Track B must prospectively define statuses including:

- adjudicated in-scope diagnosis,
- adjudicated out-of-scope diagnosis,
- insufficient information,
- unresolved diagnostic uncertainty,
- excluded for pre-specified protocol reason.

Cases must not be removed simply because MedIntel performs poorly on them.

The disposition of every excluded or non-adjudicable case must be recorded.

---

## 13. Out-of-Scope Cases

Track B should include an explicitly defined mechanism for identifying
patients whose final clinical reference diagnosis falls outside the frozen
13-condition disease-ranking scope.

Out-of-scope cases must not be forcibly mapped to the closest supported
condition.

Disease-ranking accuracy for the 13-condition classifier and scope-handling
performance must be reported separately where applicable.

The supported-scope model must not be reinterpreted as a disease-ranking
model.

---

## 14. Critical and Safety-Relevant Conditions

Safety-oriented evaluation may separately identify clinically important
conditions such as:

- pulmonary embolism,
- spontaneous pneumothorax,
- severe pneumonia,
- other prospectively defined urgent findings.

These labels must be established independently of MedIntel.

Safety sensitivity or critical-condition detection analyses must not be
presented as evidence of general diagnostic accuracy.

Knowledge-base red flags are screening-support content and are not a
reference standard.

---

## 15. Inter-Rater Agreement

Before final adjudication, Track B should preserve independent reviewer
labels so that reviewer agreement can be measured.

Agreement analyses may include:

- raw agreement,
- class-specific agreement,
- Cohen's kappa when two raters are applicable,
- an appropriate multi-rater agreement statistic when more than two
  independent raters are used.

The final study report must distinguish:

- agreement between clinicians,
- adjudicated reference labels,
- agreement between MedIntel and the adjudicated reference standard.

---

## 16. Reference-Standard Data Model

A governed Track B reference-standard record should contain at minimum:

- study case identifier,
- source dataset identifier,
- inclusion status,
- frozen-scope status,
- reviewer 1 diagnosis,
- reviewer 1 confidence,
- reviewer 2 diagnosis,
- reviewer 2 confidence,
- disagreement indicator,
- adjudication required indicator,
- final adjudicated diagnosis,
- adjudicator identifier or coded study identifier,
- adjudication confidence,
- insufficient-information indicator,
- exclusion reason if applicable,
- reference-label lock timestamp,
- protocol version.

Protected health information must not be stored in the MedIntel source-code
repository.

---

## 17. Reference-Standard Lock

Before final Track B model evaluation begins:

1. cohort inclusion and exclusion rules must be frozen,
2. reference-standard rules must be frozen,
3. disease mappings must be frozen,
4. adjudicated reference labels must be locked,
5. subgroup definitions must be frozen,
6. evaluation metrics and acceptance gates must be frozen,
7. the MedIntel system version must remain frozen.

Once the evaluation cohort and reference labels are locked, no tuning of the
frozen MedIntel system is permitted against Track B outcomes.

A subsequent system modification creates a new version requiring a new
evaluation.

---

## 18. Leakage Prevention

The following are prohibited during reference-standard creation:

- allowing model predictions to influence clinician labels,
- using test-set performance to revise disease mappings,
- using error analysis to remove difficult test cases,
- changing clinical thresholds after seeing test outcomes,
- modifying prompts or KB content based on locked evaluation cases,
- changing SafetyValidator behavior based on evaluation failures,
- relabeling cases merely to agree with model output.

Reference-standard construction and model evaluation must remain
independent.

---

## 19. Track C Clinician Review Boundary

Clinician review of MedIntel outputs is valuable for evaluating:

- usefulness,
- clarity,
- interpretability,
- missing information,
- unsafe suggestions,
- workflow burden,
- perceived clinical relevance.

However, clinician satisfaction with MedIntel output is not equivalent to
diagnostic correctness.

Track C findings must therefore remain separate from Track B diagnostic
performance.

---

## 20. Required Phase 7.3 Outputs

Phase 7.3 requires:

1. explicit Track A benchmark reference definition,
2. explicit Track B clinical reference-standard definition,
3. clinician blinding rule,
4. independent-review rule,
5. disagreement adjudication rule,
6. uncertain-case handling rule,
7. out-of-scope handling rule,
8. reference-standard lock rule,
9. leakage-prevention rule,
10. interpretation boundary between synthetic benchmarking and clinical
    validation.

No clinical-performance claim is authorized by completion of Phase 7.3.

---

## 21. Phase 7.3 Completion Boundary

Phase 7.3 is complete when the reference-standard protocol is frozen and the
following distinctions are explicit:

**Track A:** synthetic DDXPlus benchmark reference.

**Track B:** independent governed clinical reference standard with blinded
clinical adjudication.

**Track C:** clinician review and human-factors evidence.

Phase 7.3 does not itself execute Track B or Track C.

It does not establish clinical validity.

The MedIntel prototype remains **not clinically validated**.
