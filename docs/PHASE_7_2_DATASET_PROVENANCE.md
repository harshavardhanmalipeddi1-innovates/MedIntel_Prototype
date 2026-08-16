# MedIntel Phase 7.2 — Validation Dataset and Case-Set Provenance

## 1. Status

**Protocol stage:** DATASET PROVENANCE AND CASE-SET DEFINITION

**System under test:** Frozen MedIntel respiratory clinical
decision-support research prototype.

**Phase 6 frozen system commit:**

`388d847bdd7a9f3377c77beb019eac242ffc43c1`

**Phase 7.1 protocol commit:**

`527400e3970385f8b4f9c1f2b14a6eed44099997`

Phase 7.2 defines the evidence required to reconstruct and lock the
synthetic Track A evaluation cohort.

It does not establish clinical validation.

The frozen MedIntel prototype remains **not clinically validated**.

---

## 2. Dataset Source

The synthetic respiratory model was developed from the English DDXPlus
research dataset.

Repository attribution identifies:

- DDXPlus Dataset (English)
- CC BY 4.0
- patient-data source distributed separately from the model repository
- evidence metadata derived from `release_evidences.json`

The deployed repository does not contain DDXPlus patient-level training,
validation, or test records.

The expected official patient split names used by the historical
training workflow are:

- `release_train_patients.csv` or `.zip`
- `release_validate_patients.csv` or `.zip`
- `release_test_patients.csv` or `.zip`

Generic aliases such as `train.csv`, `validation.csv`, and `test.csv`
were only fallback discovery names.

---

## 3. Recovered Historical Training Package

A historical Kaggle result package was recovered locally:

`respiratory_ddx_results_v6_2_1.zip`

Recovered ZIP SHA-256:

`64106B7922DF497D27CD67A769231AC363DCB5BB2204B38D373E6066F0F2E870`

The package contains 69 ZIP entries including:

- `run_summary.json`
- `artifact_manifest_sha256.csv`
- `raw_split_summary.csv`
- `strict_overlap_summary.json`
- `duplicate_audit.json`
- `respiratory_counts_available.csv`
- `respiratory_counts_used.csv`
- `primary_stage_metrics.csv`
- `ddx_stage_metrics.csv`
- `ddx_per_condition_stage_metrics.csv`
- `partial_history_robustness_summary.csv`
- `strict_full_history_top5_predictions.csv`
- `README_RESULTS.txt`
- `portable_metadata.json`
- `primary_pathology_xgboost.json`
- `supported_scope_xgboost.json`
- `preprocessing_bundle.joblib`

The recovered package also contains historical experimental artifacts
that are not all present in the deployed repository.

Those experimental artifacts must not automatically be treated as
deployed runtime components.

---

## 4. Deployed-Core Artifact Identity

The following deployed ML artifacts are byte-identical to their
counterparts in the recovered historical Kaggle package.

### Primary respiratory model

Repository SHA-256:

`4B37CFA17566C10C3959236B7B9DFE18F6AC476295128EB06C82911BFB3C27CE`

Historical package SHA-256:

`4B37CFA17566C10C3959236B7B9DFE18F6AC476295128EB06C82911BFB3C27CE`

**Identity:** EXACT BYTE MATCH

### Supported-scope model

Repository SHA-256:

`7C6F53AFCDF82CEF5995CF97DA4FA4DABD394111F91B05CDC47305FA5A918722`

Historical package SHA-256:

`7C6F53AFCDF82CEF5995CF97DA4FA4DABD394111F91B05CDC47305FA5A918722`

**Identity:** EXACT BYTE MATCH

### Preprocessing bundle

Repository SHA-256:

`12B5BC4AFD8A9232D958C3B89BCEAFC2AEED37D3E9DA00BB02C60EB9CE9FCB90`

Historical package SHA-256:

`12B5BC4AFD8A9232D958C3B89BCEAFC2AEED37D3E9DA00BB02C60EB9CE9FCB90`

**Identity:** EXACT BYTE MATCH

This establishes direct provenance between the recovered historical
synthetic training package and the core ML artifacts used by the frozen
MedIntel deployment.

---

## 5. Portable Metadata Identity

The historical and deployed copies of `portable_metadata.json` have
different byte-level SHA-256 hashes.

Historical package:

`ED192F6A48051F024EA008BC6F707A52729EB8261D93D1F4FCBAE8E82F94D86A`

Current repository:

`9EC5CFE327740D28CEC7F1C565B081A6C0963A1AFD72C176C3B27D2945A3B56F`

A parsed structural comparison found:

`TOTAL METADATA DIFFERENCES = 0`

The following fields were confirmed semantically identical:

- version,
- primary model filename,
- scope model filename,
- all 13 class names,
- feature names,
- research warning,
- scope thresholds,
- scope policy,
- primary confidence thresholds,
- critical-consideration thresholds,
- critical-head thresholds,
- DDx model declarations,
- candidate-inclusion model declarations,
- critical-head model declarations.

Therefore the metadata difference is a byte-serialization difference,
not a semantic model-configuration difference.

---

## 6. Historical Raw Split Accounting

Recovered historical run metadata records the following raw DDXPlus
splits:

| Split | Records | Columns | Pathologies |
|---|---:|---:|---:|
| Train | 1,025,602 | 6 | 49 |
| Validation | 132,448 | 6 | 49 |
| Test | 134,529 | 6 | 49 |
| Total | 1,292,579 | 6 | 49 |

The historical required patient fields were:

- `AGE`
- `SEX`
- `PATHOLOGY`
- `EVIDENCES`
- `INITIAL_EVIDENCE`
- `DIFFERENTIAL_DIAGNOSIS`

These counts are provenance targets for a future reconstruction of the
official DDXPlus release.

A newly acquired dataset must not be accepted solely because filenames
match.

Its structure and counts must first be compared against these recovered
historical values.

---

## 7. Historical Respiratory Evaluation Cohort

The recovered run summary records:

- respiratory training records: **353,775**
- strict respiratory validation records: **46,125**
- strict respiratory test records: **46,334**
- strict full-scope validation records: **130,640**
- strict full-scope test records: **132,399**

The target Phase 7 Track A primary respiratory evaluation cohort is the
reconstructable strict respiratory test cohort, not an arbitrary new
random split.

The expected historical strict respiratory test count is:

**46,334 cases**

This expected count is an integrity check, not a rule to force or
truncate a different dataset into the historical size.

---

## 8. Duplicate and Cross-Split Profile Audit

The historical run used exact input-profile auditing based on:

- age,
- sex,
- evidence history,
- initial evidence.

Raw release audit:

- train records: 1,025,602
- train unique profiles: 1,012,347
- validation records: 132,448
- validation unique profiles: 132,373
- test records: 134,529
- test unique profiles: 134,428
- train/validation profile overlap: 1,788
- train/test profile overlap: 1,965
- validation/test profile overlap: 172

The strict filtering stage recorded:

- validation profiles removed against full training: **1,808**
- test profiles removed against training or strict validation: **2,130**

No Phase 7 reconstructed synthetic benchmark may ignore this filtering
because doing so would change the historical evaluation definition.

---

## 9. Requirement for All Three DDXPlus Splits

The original patient split files are not currently available locally.

The historical strict evaluation cannot be reconstructed from the test
file alone.

All three official patient splits are required because:

1. training profiles are needed to identify evaluation overlap,
2. validation profiles must first be filtered against training,
3. test profiles must then be filtered against both training and the
   strict validation profile set.

Therefore Track A reconstruction requires:

- official train split,
- official validation split,
- official test split.

No model retraining is required merely to reconstruct the evaluation
cohort.

---

## 10. Reconstructed Track A Acceptance Checks

Before any new synthetic evaluation begins, a reacquired DDXPlus
release must pass all applicable checks below.

### Source checks

- dataset obtained from the documented DDXPlus source,
- source location and acquisition date recorded,
- original filenames recorded,
- SHA-256 generated for every acquired source file.

### Structural checks

Expected raw counts:

- train: 1,025,602
- validation: 132,448
- test: 134,529
- total: 1,292,579

Expected raw pathology count:

- 49

Expected required columns:

- AGE
- SEX
- PATHOLOGY
- EVIDENCES
- INITIAL_EVIDENCE
- DIFFERENTIAL_DIAGNOSIS

### Strict-cohort checks

The historical input-profile overlap procedure must be reproduced.

Expected historical strict respiratory counts:

- validation: 46,125
- test: 46,334

Expected strict full-scope counts:

- validation: 130,640
- test: 132,399

Any discrepancy must stop automatic acceptance and be investigated.

The evaluator must not silently sample, pad, duplicate, or discard
records merely to force the expected historical counts.

---

## 11. Historical Predictions

The recovered package contains:

`strict_full_history_top5_predictions.csv`

This provides historical case-level outputs including:

- test row,
- age,
- sex,
- ground-truth pathology,
- primary Top-1 prediction,
- primary confidence,
- primary Top-5,
- DDx Top-5,
- DDx relevance values,
- critical-consideration outputs.

This historical file is valuable for regression comparison.

However, it does not contain the complete raw patient evidence history
required to replay each case through the current MedIntel workflow.

Therefore it is not itself a replacement for the original DDXPlus
patient test records.

---

## 12. Historical Experimental Artifacts Versus Deployed Runtime

The recovered historical package contains:

- 13 DDx probability models,
- 4 candidate-inclusion models,
- 5 critical-pathology heads.

The current deployed repository does not contain every historical
experimental model artifact.

Phase 7 validation must evaluate the actual frozen deployed runtime.

Historical components absent from the deployed runtime may be analyzed
only as historical or artifact-level exploratory components.

They must not be silently copied into the deployed workflow in order to
improve validation performance.

The supported-scope model must never be reinterpreted as a
disease-ranking model.

---

## 13. Frozen Disease Scope

The deployed respiratory classifier supports exactly 13 classes:

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

Track A disease-ranking metrics must clearly distinguish this
13-condition closed-world scope from any wider DDXPlus differential
coverage analysis.

---

## 14. Data Storage Rule

Reacquired DDXPlus patient files must not be committed to the MedIntel
Git repository.

A dedicated local validation-data location should be used.

The data location, hashes, source, acquisition date, and file sizes must
be recorded in the Phase 7 validation manifest.

Evaluation code may reference the local data path through configuration
or an environment variable rather than embedding patient records in the
repository.

---

## 15. No-Tuning Rule

The frozen system must not be tuned against the reconstructed Track A
test cohort.

Track A results must not be used during the same validation run to
modify:

- model weights,
- preprocessing,
- disease mappings,
- thresholds,
- prompts,
- knowledge-base content,
- SafetyValidator rules,
- reasoning retry behavior,
- candidate-selection behavior.

A system change creates a new version requiring a new validation run.

---

## 16. Phase 7.2 Provenance Classification

Current provenance status is:

**RECOVERED HISTORICAL MODEL PROVENANCE WITH PATIENT-DATA
RECONSTRUCTION REQUIRED**

Established:

- historical synthetic run package recovered,
- recovered package SHA-256 recorded,
- core deployed model artifact identity proven byte-for-byte,
- preprocessing identity proven byte-for-byte,
- deployed metadata semantics verified identical,
- raw split counts recovered,
- historical strict respiratory cohort counts recovered,
- duplicate and overlap-removal counts recovered,
- historical case-level prediction export recovered.

Not yet established:

- original patient split file bytes,
- original patient split SHA-256 values,
- reconstructed strict test patient records on the present machine.

Therefore a future reacquisition of the official DDXPlus files must be
described as a **reconstructed official-release Track A cohort** unless
independent evidence later proves exact original input-file identity.

---

## 17. Phase 7.2 Completion Boundary

Phase 7.2 defines and freezes the validation dataset provenance and
case-set reconstruction rules.

It does not claim that Track A has been executed under Phase 7.

It does not claim external clinical validity.

It does not claim prospective clinical performance.

Phase 7.2 completion authorizes controlled acquisition and reconstruction
of the synthetic validation case set under the frozen rules above.

The frozen MedIntel system remains **not clinically validated**.
