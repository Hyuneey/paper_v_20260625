# TASK-039BR2 Report

## Status

`passed_hai_2305_continuous_step_single_process_freeze`

Execution code commit:
`4461db42b78b573b9f8b10979d75d0e0912bab32`

Execution receipt hash:
`fe9fdf32b0c14218ad27c55b1798a977dce71aa27365e442048059a48bc29d5d`

## Frozen Inputs

The execution bound the verified HAI manifest, TASK-039A/039AR provenance,
TASK-039BR0 eligibility and morphology records, and TASK-039BR1 protocol. The
protocol bundle hash was
`5e57e1103b95d8cb24bf55f9ff85a989773dbe05816479dc79c493de044a7bbd`;
the config hash was
`8a82c7fc0924cd4bc40c83e783eb51f43edf8b0a3ac3948bf4042b93e5370573`.

Only the frozen P1/P3 source and target columns in verified train1, train2, and
train3 were read. All source and target scales came from train1 and train2.
Train3 was replayed without retuning. Train4 contributed only public structural
identity needed for the future normal-guard split.

## Results

| Metric | P1 Boiler | P3 Water Treatment |
| --- | ---: | ---: |
| Valid source thresholds | 12 | 2 |
| Eligible continuous targets | 12 | 3 |
| Fit-supported directional relations | 69 | 0 |
| Calibration-confirmed directional relations | 65 | 0 |
| Distinct confirmed sources | 9 | 0 |
| Distinct confirmed targets | 10 | 0 |
| Fit-to-calibration transfer rate | 0.9420289855072463 | 0.0 |
| Median calibration isolated-event support | 304.0 | 0.0 |
| Feasibility gate | passed | failed |

P1 retained 58 direction-unstable and 161 fit-unsupported records, plus 4
fit-supported records that conflicted on train3. P3 retained 9
direction-unstable and 3 fit-unsupported records. These negative outcomes are
preserved rather than filtered from the evidence trail.

Exactly one process passed the frozen gate, so the selection policy chose P1
with reason `only_P1_feasible`. No weighted score or Pareto tie-break was used.
The process-freeze artifact hash is
`f263d23ceda5ab5ff3c7459e56669ab1dadd7d30cd2243ad8971301990a86325`.

## Access And Authority

The data-access audit records zero prohibited accesses. Test feature values,
labels, attack summaries, private custody, train4 feature values, and P2/P4
feature values were not accessed. Raw rows, raw windows, event timestamps,
absolute local paths, and private ledger contents are absent from public
artifacts. Six private scientific ledgers were written outside the repository
and their self-hashes were verified without emitting their contents.

Rule v1, Verifier v1, and Runtime v1 are unchanged. Rule v2 was not created.
Feasibility parameters were not promoted to canonical calibration or runtime
parameters. TASK-039C is authorized only for P1 candidate-universe and graph
evidence work; the production graph-ranking backend remains unresolved.

The authoritative result was produced only from the clean execution code
commit above. Earlier incomplete or failed-closed local runs were discarded;
their outputs were not reused.

## Verification

- TASK-039BR2 targeted tests: 43 passed.
- TASK-039BR1 regressions: 34 passed.
- TASK-039BR0 regressions: 24 passed.
- Frozen TASK-039B regressions: 27 passed from commit
  `6543ca5b88779262d01c5e0c24e51216dd0835e9`.
- TASK-039A/TASK-039AR regressions: 37 passed.
- P0/P1A/P1B/P1C/P1D and v1-data regressions: 156 passed.
- TASK-032A-F frozen hash and replay regressions: 106 passed.
- Lightweight candidate and relation-profiling regressions: 22 passed.
- Guarded discovery loaded 581 tests: 544 runnable tests passed, with 37 known
  optional import errors (`jsonschema` 19, `pytest` 16, Torch/PyG 2) and zero
  unexplained errors.
- Syntax compilation passed for 405 tracked public Python files.
- Allowlisted parsing passed for 403 JSON files: 393 tracked inputs and 10 new
  BR2 result JSON files.
- Draft 2020-12 meta-validation passed for all 55 v6 schemas. Nine direct BR2
  artifacts and three selected-process split manifests passed instance
  validation.
- All 11 BR2 public JSON self-hashes and all 6 external private-ledger
  self-hashes passed.
- `pip check`, `git diff --check`, public leak scans, and frozen Rule v1,
  Verifier v1, Runtime v1, and runtime-authority blob checks passed.

## Claim Boundary

TASK-039BR2 executes the preregistered continuous-step delayed-response
feasibility protocol using only verified normal HAI 23.05 train1-train3 data.

The selected process is frozen because it provides the more defensible
normal-only foundation for the bounded continuous-step MVP under the frozen
feasibility and Pareto policy.

TASK-039BR2 does not establish physical causality, create Rule v2, construct
the final candidate graph, train GDN, create final runtime parameters, access
attack data, generate a rule, run a detector, or establish anomaly-detection
performance.
