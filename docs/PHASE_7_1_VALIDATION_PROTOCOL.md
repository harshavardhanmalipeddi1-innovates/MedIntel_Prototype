# MedIntel Phase 7.1 ? Validation Scope and Protocol

## 1. Status

**Protocol status:** PRE-EXECUTION VALIDATION PROTOCOL

**System under test:** MedIntel Phase 6 frozen respiratory clinical
decision-support research prototype.

**Frozen Git tag:** `medintel-phase6-prototype-freeze`

**Frozen commit:**
`388d847bdd7a9f3377c77beb019eac242ffc43c1`

The system must remain frozen while a validation dataset is being
evaluated. Changes to model weights, preprocessing, disease mappings,
knowledge-base semantics, prompts, safety rules, thresholds, or workflow
logic require a new version and a new validation run.

This protocol does not itself establish clinical validity.

The frozen MedIntel prototype is **not clinically validated**.

---

## 2. Intended Use Boundary

MedIntel is being evaluated as a **clinician-facing respiratory
decision-support research prototype**.

The prototype may:

- accept structured respiratory patient information,
- generate XGBoost-ranked respiratory differential candidates,
- retrieve disease knowledge,
- generate constrained MedGemma reasoning around existing candidates,
- generate verification support,
- produce treatment-support drafts for clinician review.

The prototype must not:

- autonomously establish a final diagnosis,
- autonomously prescribe treatment,
- replace clinician judgment,
- treat model scores as real-world clinical probabilities,
- bypass mandatory doctor review.

Final diagnosis and treatment decisions remain with the treating
clinician.

---

## 3. Frozen System Under Test

The Phase 7 validation target is the complete deployed workflow frozen
at the Phase 6 tag, including:

1. structured assessment preparation,
2. respiratory feature construction,
3. preprocessing artifacts,
4. primary XGBoost respiratory disease ranking,
5. differential candidate generation,
6. disease knowledge retrieval,
7. local MedGemma reasoning,
8. deterministic evidence semantic normalization,
9. reasoning safety validation,
10. controlled one-time safety-compliance regeneration,
11. verification support,
12. treatment-support draft generation,
13. mandatory doctor-review status.

Validation must use the behavior of the deployed workflow.

Experimental models or files referenced by historical training metadata
must not be counted as deployed components when the corresponding
runtime artifact is absent.

Missing experimental artifacts must not be fabricated, copied,
retrained, or substituted solely to improve validation results.

---

## 4. Supported Respiratory Disease Scope

The frozen respiratory classifier supports these 13 disease classes:

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

Performance outside this disease set must not be described as validated
unless a separate protocol explicitly evaluates that use.

---

## 5. Validation Questions

Phase 7 will answer five separate questions.

### Q1 ? Diagnostic ranking

When the reference diagnosis belongs to the supported 13-condition
scope, how often does the frozen system place it at useful positions in
the ranked differential?

### Q2 ? Differential quality

When a reference differential diagnosis is available, how well does the
system recover and rank clinically relevant alternatives?

### Q3 ? Robustness

How does performance change when patient history is incomplete or
available evidence is reduced?

### Q4 ? Safety behavior

Does the full workflow preserve candidate identity, clinician authority,
red-flag semantics, and fail-closed behavior?

### Q5 ? External clinical generalization

How does the frozen system perform on appropriately governed,
real-world respiratory encounters that were not used for model
development?

Questions Q1?Q4 can first be investigated using the locked synthetic
benchmark.

Q5 requires a separate real-world external evaluation and is necessary
before making claims of clinical validation.

---

## 6. Validation Tracks

### Track A ? Locked Synthetic Benchmark

Purpose:

- reproduce algorithmic performance,
- verify ranking behavior,
- detect regression,
- measure robustness,
- measure deterministic safety behavior.

Source:

- DDXPlus test data or another exact held-out synthetic split whose
  provenance can be reconstructed.

Important:

Track A is an **algorithm-development benchmark only**.

Passing Track A must not be described as clinical validation.

Before execution, the evaluator must verify that the selected test cases
were not used for training, threshold selection, prompt tuning, or other
model-development decisions.

Duplicate or exact input-profile overlap with training/validation data
must be audited where source data permit.

### Track B ? External Retrospective Clinical Evaluation

Purpose:

- investigate real-world generalization.

Requirements must be finalized before execution, including:

- clinical data source,
- permitted use and governance,
- de-identification procedure,
- inclusion criteria,
- exclusion criteria,
- target population,
- reference-standard definition,
- disease-label mapping,
- feature/evidence mapping,
- missing-data handling,
- clinician adjudication procedure where required.

Applicable institutional, ethical, privacy, and data-governance
requirements must be resolved before real patient data are used.

No model or prompt tuning may be performed on the final external
evaluation cohort.

### Track C ? Clinician Review of Generated Reasoning

Purpose:

Evaluate the clinical quality of the decision-support presentation,
separately from XGBoost ranking accuracy.

Clinician review should assess:

- evidence grounding,
- factual consistency,
- unsupported inference,
- contradictory reasoning,
- missing-information correctness,
- red-flag semantics,
- potentially harmful wording,
- usefulness for differential review,
- appropriateness of uncertainty,
- preservation of clinician authority.

Automated structural checks alone are not sufficient evidence of
clinical reasoning quality.

---

## 7. Reference Standard

### Synthetic evaluation

For DDXPlus:

- `PATHOLOGY` is the reference final pathology for primary
  classification/ranking evaluation.
- the official `DIFFERENTIAL_DIAGNOSIS` field is the reference source
  for differential-ranking evaluation when available.

These are synthetic reference labels and must not be represented as
real-world clinician adjudication.

### External clinical evaluation

The real-world reference standard must be specified and frozen before
external evaluation begins.

The protocol must record:

- source of the final reference diagnosis,
- whether the reference is single-label or multi-label,
- whether adjudication is required,
- handling of uncertain diagnoses,
- handling of diagnoses outside the 13-condition system scope,
- mapping from source terminology to MedIntel disease classes.

Cases with unresolved reference-standard ambiguity must be handled
according to a pre-specified rule rather than changed after model output
is inspected.

---

## 8. Primary Diagnostic-Ranking Endpoints

The following metrics will be calculated where applicable.

### 8.1 Top-1 performance

- Top-1 accuracy
- per-condition Top-1 recall

### 8.2 Top-K inclusion

- Top-3 reference-diagnosis inclusion
- Top-5 reference-diagnosis inclusion
- per-condition Top-3 recall
- per-condition Top-5 recall

When fewer than K candidates are returned, unreturned positions must not
be artificially padded with favorable candidates.

### 8.3 Candidate yield

Report:

- number of candidates returned per case,
- proportion of cases returning at least one candidate,
- proportion returning 1, 2, 3, 4, or 5 candidates,
- degraded/no-reasoning frequency separately from disease-ranking
  availability.

Candidate yield must be reported alongside Top-K metrics to prevent
apparent performance improvements caused by selective output behavior.

---

## 9. Differential-Ranking Endpoints

When an official/reference differential is available, evaluate:

- NDCG,
- LRAP where applicable,
- reference differential label recall,
- probability-mass capture where the reference provides weights,
- per-condition candidate recall.

Closed-world 13-condition performance and coverage of the full reference
differential must be reported separately.

A result must not imply full differential coverage when the reference
contains diseases outside the supported 13-condition scope.

---

## 10. Robustness Endpoints

Evaluate performance under controlled evidence reduction where the
dataset supports it.

At minimum:

- full available history,
- partial-history conditions,
- initial-evidence-only condition.

For randomized evidence removal:

- use fixed pre-specified seeds,
- preserve the initial-evidence marker,
- report results across multiple seeds,
- do not select the best seed after evaluation.

Report diagnostic-ranking degradation by evidence-retention level.

---

## 11. Disease-Stratified Safety Evaluation

The following clinically important respiratory classes require explicit
per-condition reporting:

- Bronchospasm / acute asthma exacerbation
- Pneumonia
- Pulmonary embolism
- Spontaneous pneumothorax
- Tuberculosis

This reporting requirement does not imply that a separate deployed
critical-pathology model exists for each disease.

Evaluation must distinguish:

- actual deployed workflow behavior,
- experimental model artifacts,
- unavailable artifacts.

Unavailable experimental components must be reported as unavailable,
not silently reconstructed during validation.

---

## 12. Workflow Safety Endpoints

The end-to-end workflow must be evaluated for deterministic safety
properties.

Report counts and rates for:

### 12.1 Candidate preservation

- candidate-count alteration,
- disease-name alteration,
- rank alteration by MedGemma.

Expected deterministic safety target:

**0 accepted violations.**

### 12.2 Doctor-review preservation

Measure cases where `requires_doctor_review` is not true.

Expected deterministic safety target:

**0 accepted bypasses.**

### 12.3 Authoritative diagnostic language

Measure outputs accepted by the workflow that contain wording prohibited
by the frozen SafetyValidator.

Expected deterministic safety target:

**0 accepted violations.**

### 12.4 Knowledge-base red-flag semantics

Measure knowledge-base screening items incorrectly represented as
patient-present findings.

Expected deterministic safety target:

**0 accepted semantic conversions.**

### 12.5 Unsupported candidate introduction

Measure LLM-generated diseases not present in the upstream frozen
differential.

Expected deterministic safety target:

**0 accepted unsupported candidates.**

### 12.6 Compliance retry behavior

Report:

- first-attempt safety pass rate,
- one-time compliance-retry invocation rate,
- retry success rate,
- retry failure rate,
- safe degraded-response rate.

A degraded response is not automatically a safety failure; it must be
reported separately because fail-closed degradation may be the correct
safe behavior.

---

## 13. MedGemma Reasoning Evaluation

Automated validation will measure structural safety and evidence
grounding.

It must not be used alone to claim that generated clinical reasoning is
medically correct.

Automated checks include:

- candidate identity preserved,
- rank preserved,
- doctor review preserved,
- no prohibited authoritative wording,
- no raw evidence-code leakage in normalized supporting findings,
- explicitly supplied evidence not falsely reported as missing,
- no fake missing-information sentinel,
- red-flag screening semantics preserved.

Clinical correctness of the generated rationale requires the separate
clinician-review track.

---

## 14. Subgroup Reporting

Where sample size permits, report exploratory results by:

- disease,
- sex,
- age group,
- evidence-completeness level.

Subgroup results are exploratory unless the subgroup hypotheses and
sample-size requirements are pre-specified.

Small subgroup counts must be reported rather than hidden.

---

## 15. Out-of-Scope and Non-Respiratory Cases

If non-respiratory cases are evaluated, report them separately.

Possible measurements include:

- unsupported-case acceptance,
- unsupported-case withholding,
- false acceptance,
- false rejection.

These metrics may be described as deployed system metrics only if the
evaluated runtime actually invokes the corresponding scope-gating path.

If a scope model exists only as an artifact but is not part of the
evaluated deployed workflow, its results must be labeled
**artifact-level exploratory evaluation**.

A binary scope model must never be interpreted as a disease-ranking
model.

---

## 16. Pre-Specified Performance Gates

Clinical performance thresholds must not be invented after viewing the
validation results.

Before Track B begins, the team must freeze:

- primary endpoint,
- minimum acceptable performance threshold,
- confidence-interval method,
- required sample size,
- critical-disease acceptance criteria,
- allowable missing-data rate,
- subgroup analysis plan,
- failure criteria.

Until those values are prospectively specified, external results may be
reported descriptively but must not be labeled as having passed a
clinical-validation acceptance gate.

The deterministic software safety invariants defined in Section 12 are
already fixed at zero accepted violations.

---

## 17. No-Tuning Rule

After an evaluation cohort is locked:

Do not use its results to modify:

- XGBoost model weights,
- preprocessing artifacts,
- class mappings,
- thresholds,
- knowledge-base content,
- prompts,
- SafetyValidator rules,
- compliance-retry instructions,
- output-selection logic.

If a modification is necessary:

1. record the failure,
2. close the current validation run,
3. create a new system version,
4. define a new evaluation cohort or otherwise preserve an untouched
   final test set,
5. repeat validation under the new version.

---

## 18. Validation Manifest

Every validation run must record at least:

- validation run ID,
- timestamp,
- Git commit SHA,
- Git tag if applicable,
- Docker image identifiers,
- model artifact hashes,
- preprocessing artifact hash,
- MedGemma model identifier,
- llama.cpp image digest,
- prompt version/hash,
- knowledge-base version/hash,
- dataset identifier,
- dataset hash where permitted,
- case count,
- inclusion/exclusion summary,
- mapping version,
- evaluation-script version,
- random seeds,
- protocol deviations.

---

## 19. Required Validation Outputs

Phase 7 execution should eventually generate machine-readable artifacts
such as:

- `validation_manifest.json`
- `case_level_results.csv`
- `primary_ranking_metrics.json`
- `primary_per_condition_metrics.csv`
- `differential_ranking_metrics.json`
- `robustness_metrics.csv`
- `safety_metrics.json`
- `subgroup_metrics.csv`
- `failure_cases.csv`
- `protocol_deviations.md`
- `validation_report.md`

No metric should exist only as terminal output.

---

## 20. Failure Analysis

Every validation failure should be assigned to a reproducible category
where possible.

Suggested categories:

- reference diagnosis absent from supported scope,
- evidence mapping failure,
- insufficient input evidence,
- primary ranking miss,
- candidate truncation,
- knowledge retrieval issue,
- reasoning schema failure,
- reasoning safety rejection,
- compliance retry failure,
- safe degraded response,
- red-flag semantic issue,
- unsupported inference,
- dataset/reference-standard ambiguity.

Failure cases must be retained for analysis without changing the frozen
model during the same validation run.

---

## 21. Interpretation Boundary

A successful synthetic evaluation means:

> The frozen MedIntel implementation demonstrates measured performance
> on the specified synthetic benchmark.

It does not mean:

- clinically validated,
- diagnostically proven in real patients,
- safe for unsupervised use,
- treatment effective,
- regulatory approved,
- production ready.

A real-world retrospective evaluation may provide evidence of clinical
generalization, but the strength of that evidence depends on the dataset,
reference standard, study design, sample size, missingness, mapping
quality, and clinician adjudication process.

---

## 22. Phase 7.1 Completion Criteria

Phase 7.1 is complete when:

1. this protocol is reviewed and frozen,
2. the intended-use boundary is accepted,
3. the 13-condition scope is confirmed,
4. the actual deployed artifact inventory is recorded,
5. Track A dataset provenance is established,
6. Track B data-source strategy is defined,
7. reference-standard rules are defined,
8. performance gates for real-world validation are prospectively
   specified before Track B evaluation,
9. validation outputs and manifest requirements are frozen,
10. no Phase 6 frozen component has been changed.

Phase 7.1 completion is a **protocol milestone**, not a clinical
validation result.
