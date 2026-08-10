# TASK-039BR2 Existing Result Independent Audit

## Decision

- Status: `passed_br2_existing_result_audit`
- Merge recommendation: `READY_FOR_FAST_FORWARD_TO_MAIN`
- Audited BR2 result: `c417dec4b35f900ac5a614e57716b44991a3b0e0`
- Execution code commit: `4461db42b78b573b9f8b10979d75d0e0912bab32`
- Selected process: `P1`
- Selection reason: `only_P1_feasible`
- Blocking findings: none

This was a read-only scientific and implementation audit. It did not rerun
the real HAI feasibility execution, change an existing BR2 artifact, inspect
attack data, or update `main`.

## Branch And Lineage

The audit began with:

- `main` and `origin/main` at
  `7c046a5988156f194fefc5953d99ffa5b8a38244`;
- `origin/task-039br2-continuous-step-feasibility` at
  `c417dec4b35f900ac5a614e57716b44991a3b0e0`;
- merge base equal to the authoritative main commit;
- branch distance equal to zero commits behind and six commits ahead.

The complete BR2 lineage is:

| Order | Commit | Parent | Subject | Scientific scope |
|---:|---|---|---|---|
| 1 | `97689ff291b817b8befdc100da2a4331c1843f6c` | `7c046a5988156f194fefc5953d99ffa5b8a38244` | TASK-039BR2 implement continuous-step feasibility | Protocol execution implementation, schemas, config, CLI, synthetic tests and pending documentation |
| 2 | `2500062bc54189b335041dbca3ece5292b5dbfd0` | `97689ff291b817b8befdc100da2a4331c1843f6c` | TASK-039BR2 optimize protocol-equivalent execution | Protocol-equivalent source implementation and synthetic-test optimization |
| 3 | `bd87247f8b101f66daca77efe9a34cbbb85a123d` | `2500062bc54189b335041dbca3ece5292b5dbfd0` | TASK-039BR2 correct public boundary projection | Public boundary implementation and tests |
| 4 | `4461db42b78b573b9f8b10979d75d0e0912bab32` | `bd87247f8b101f66daca77efe9a34cbbb85a123d` | TASK-039BR2 harden structural public scan | Final execution code and boundary-test hardening |
| 5 | `9763c11cf8d2e16bc58daec0ee7c4a3e2a0eba0c` | `4461db42b78b573b9f8b10979d75d0e0912bab32` | TASK-039BR2 extend additive schema regression | One additive schema-registry regression assertion only |
| 6 | `c417dec4b35f900ac5a614e57716b44991a3b0e0` | `9763c11cf8d2e16bc58daec0ee7c4a3e2a0eba0c` | TASK-039BR2 evaluate HAI continuous-step feasibility | Sanitized result artifacts and final status documentation only |

The execution receipt binds every result to commit `4461db42...`. After that
commit, `9763c11...` changed only
`tests/test_task039p1c_schema_and_boundaries.py`; the result commit changed
only sanitized reports and documentation. No source, scientific config or
schema changed after the authoritative execution-code commit. No unrelated
commit entered the six-commit lineage.

The deterministic `creation_metadata.created_at` value is configuration
metadata, not wall-clock proof of execution order. Git ancestry, the receipt's
`execution_code_commit`, and the result-only final commit establish ordering.

## Frozen Inputs

The following identities parsed, self-hashed and matched their frozen values:

- BR1 protocol bundle:
  `5e57e1103b95d8cb24bf55f9ff85a989773dbe05816479dc79c493de044a7bbd`;
- BR1 config:
  `8a82c7fc0924cd4bc40c83e783eb51f43edf8b0a3ac3948bf4042b93e5370573`;
- dataset manifest ID:
  `5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2`;
- BR0 decision:
  `3eceafb47742af9fc1be5dba82f148d33e31ba3095ba4b8a2d513ab9d4632a7b`;
- BR0 readiness:
  `c1968c53d605756cd9d16f72306c730fcf6a9b3ceaf61368eba78157bb84f7a2`;
- BR0 source-exclusion ledger binding:
  `3df659ddfa0971933643f54aa203b207679ec0bedc4ed3b58268ce9cd7b52d4a`;
- BR0 morphology-ledger binding:
  `3cef789579ca54b4b829a381db7763feb3b1c4ee5b53e6ca61015f5d5aec25a3`.

## Frozen Protocol Compliance

Static code tracing and the independently rerun BR1/BR2 synthetic tests
established the following:

| Rule | Audit result | Implementation evidence |
|---|---|---|
| Fit-only scales | Passed | Multi-file scale derivation pools only within-file differences; source and target fit sequences are restricted to train1 and train2. |
| No cross-file windows | Passed | Source windows and target windows are evaluated inside one file-local sequence. |
| Source scale | Passed | `max(1.4826 * MAD(within-file dx), 1e-12)` is exact. |
| Source windows | Passed | `median(x[t-5:t])`, `median(x[t:t+5])`, and post minus pre amplitude are exact. |
| Minimum amplitudes | Passed | Fewer than 20 nontrivial amplitudes produces no threshold. |
| Q75 | Passed | Position is `0.75 * (n - 1)` with linear interpolation. |
| Source threshold | Passed | `max(5 * source_noise_scale, Q75(A_positive))` is exact. |
| Stability tolerance | Passed | `max(3 * source_noise_scale, 0.10 * source_step_threshold)` is exact. |
| Stability gate | Passed | Both pre and post fractions must be at least `0.80`. |
| Refractory clustering | Passed | File-local single-link clustering uses 10 seconds and retains largest absolute amplitude, then earliest index. |
| Cross-source isolation | Passed | Another retained source event within inclusive `+/-2` seconds makes the event non-isolated. |
| Target horizons | Passed | Only `1, 5, 10, 30, 60` seconds are accepted. |
| Target response | Passed | `median(y[t+h:t+h+3]) - median(y[t-5:t])` is exact and right-censored at file boundaries. |
| Direction separation | Passed | `step_up`/`step_down` and `increase`/`decrease` remain separate. |
| Direction ties | Passed | Selected consistency must be strictly greater than the opposite direction in both fit files; equality in either file fails agreement. |
| Ranking | Passed | Consistency, effect ratio, shortest horizon, then lexicographic exact tie only. |
| No lower fallback | Passed | Exactly one ranked candidate is gate-tested; failure is retained as `fit_unsupported` and does not search a lower-ranked candidate. |
| Fit gate | Passed | `20`, `5`, `5`, `0.70`, `0.60`, `0.60`, `2.0`, and direction agreement are unchanged. |
| Train3 confirmation | Passed | Train3 receives the frozen source direction, target direction, horizon and fit-derived source/target parameters; the confirmation gate is `5`, `0.60`, `1.0`, strict direction preservation and no retuning. |
| Negative confirmation | Passed | Every one of the 69 P1 fit-supported records has a train3 record: 65 confirmed and 4 conflicts. |
| Relation identity | Passed | Deduplication uses source, source direction, target and target direction; horizon does not inflate counts. |
| Process gate | Passed | Both processes use the same BR1 gate. Exactly one feasible process is selected before Pareto logic. |

Primary implementation locations are
`src/paperworks/feasibility/hai_continuous_step_v1.py:876` for file-local
scales, `:908` for source parameters, `:948` for event extraction, `:990` for
isolation, `:1020` for target response, `:1050` for strict direction
agreement, `:1133` for ranking, `:1150` for the fit gate, `:1163` for train3
confirmation, `:1221` for relation identity, and `:1932` through `:2054` for
the execution-to-ledger-to-metric path. The frozen BR1 gates remain in
`src/paperworks/v6/continuous_step_protocol_v1.py:873` through `:972`.

## Private Ledger Audit

All six private BR2 ledgers were locally available. Their self-hashes matched
the six ordered hashes in execution receipt
`fe9fdf32b0c14218ad27c55b1798a977dce71aa27365e442048059a48bc29d5d`.
The audit parsed them only to verify self-hashes, authority fields and aggregate
counts; it printed or copied no private record, event index or value.

Independent aggregation from the source-parameter and relation ledgers
reproduced:

| Metric | P1 | P3 |
|---|---:|---:|
| Valid source thresholds | 12 | 2 |
| Eligible targets | 12 | 3 |
| Fit-supported directional relations | 69 | 0 |
| Calibration-confirmed relations | 65 | 0 |
| Calibration conflicts | 4 | 0 |
| Distinct confirmed sources | 9 | 0 |
| Distinct confirmed targets | 10 | 0 |
| Transfer rate | `65 / 69 = 0.9420289855072463` | `0.0` |
| Median calibration isolated support | 304 | 0 |

The serialized P1 transfer value equals the host-language result of `65 / 69`.
The process reports therefore bind to derived ledger aggregates rather than
hard-coded result counts.

The Pareto-only metadata fields `manual_metadata_coverage` and
`metadata_unresolved_ratio` are frozen lineage constants in the execution
implementation rather than recomputed from the BR2 relation ledgers. This is a
nonblocking traceability limitation: Pareto comparison was not entered because
P1 alone passed the feasibility gate.

## Process Selection And Authority

The process-selection artifact self-hash is
`115407ccc97dc6ff84b96a05c45ed2a3f394d896ea865d719ef67ca20534fcff`.
It records:

- `selected_process_id = P1`;
- `excluded_process_id = P3`;
- `selection_reason = only_P1_feasible`;
- `weighted_score_used = false`.

P1 passes every BR1 feasibility condition. P3 fails the same gate because it
has no fit-supported or confirmed relation and no distinct confirmed source or
target. Because exactly one process is feasible, Pareto dominance is not the
selection basis.

Process freeze
`f263d23ceda5ab5ff3c7459e56669ab1dadd7d30cd2243ad8971301990a86325`
limits TASK-039C authorization to P1 candidate-universe and graph-evidence
work. It grants no Rule v2, rule construction, Agent, verifier, runtime,
detector, outer-validation or sealed-evaluation authority.

## Data And Public Boundaries

Data-access artifact
`9f64492c34be4df724aa0fc9ac96e87354693e5b93f791ae0c4bf65abf675c6c`
records train1, train2 and train3 as the only opened feature-value files. It
records false for train4 feature values, test feature values, label values,
attack summaries, private custody and P2/P4 feature values, with zero
prohibited accesses.

The implementation treats train4 through frozen manifest and structural
records only (`hai_continuous_step_v1.py:1416`); it does not open train4
feature values. The access ledger rejects train4, test, label, summary,
custody, attack and unauthorized process-column access before value parsing.

The public-boundary scanner passed all 11 BR2 JSON artifacts. A second scan of
all 25 BR2 public text/result paths found no local absolute path, credential,
authorization header, signed URL or private key. Branch-diff metadata found no
restricted path, raw dataset file or binary payload. Public artifacts contain
no raw value, raw window, event index, event timestamp, private-ledger content,
credential or attack detail.

## Parameter And Legacy Authority

Every private source and target parameter record has:

- `parameter_class = feasibility_screening`;
- fit-only provenance;
- no final-parameter authority;
- no runtime authority.

The execution receipt records `final_parameters_created = false` and
`rule_v2_created = false`. The BR2 source does not construct or import
`CalibrationParameterV1`, create a runtime authorization receipt, or implement
Rule v2.

Rule v1, Verifier v1, Runtime v1 and runtime-authority Git blob IDs are exactly
unchanged from main. All 106 TASK-032A-F accepted-rule, authorization and
deterministic replay regressions passed independently.

## Independently Rerun Checks

- TASK-039BR2 targeted tests: 43 passed.
- TASK-039BR1 regressions: 34 passed.
- TASK-039BR0 regressions: 24 passed.
- Frozen TASK-039B regressions: 27 passed from detached commit
  `6543ca5b88779262d01c5e0c24e51216dd0835e9`.
- TASK-039A/TASK-039AR regressions: 37 passed.
- P0/P1A/P1B/P1C/P1D and v1-data regressions: 156 passed.
- TASK-032A-F regressions: 106 passed.
- Lightweight candidate and relation-profiling regressions: 22 passed.
- Guarded discovery loaded 581 tests: all 544 runnable tests passed; 37 known
  optional import errors were classified as jsonschema 19, pytest 16 and
  Torch/PyG 2, with zero unexplained errors.
- Syntax compilation passed for 405 Git-tracked public Python files.
- Allowlisted JSON parsing passed for 403 tracked files.
- Draft 2020-12 meta-validation passed for all 55 v6 schemas.
- Instance validation passed for nine direct public BR2 artifacts and three
  selected-process split manifests.
- All 11 BR2 public JSON self-hashes passed.
- All six private-ledger self-hashes and receipt bindings passed.
- `pip check`, branch `git diff --check`, restricted-path scans, public leak
  scans and frozen canonical blob comparisons passed.

No dependency was installed or upgraded.

## Receipt-Only Historical Claims

The audit did not repeat the real HAI execution. The following remain verified
from the committed execution receipt/access artifact plus static enforcement,
not from a new observation of the historical run:

- the historical physical file-open sequence;
- the historical rehashing of HAI train1 through train3;
- the absence of a prohibited access attempt during that historical process;
- the historical execution's wall-clock timing.

This limitation is required by the audit authorization and is nonblocking
because the code and frozen protocol are reproducible, all public lineage and
self-hash bindings pass, and the locally retained private ledgers independently
reproduce the reported scientific aggregates.

## Conclusion

`passed_br2_existing_result_audit`

No blocking protocol, lineage, data-boundary, process-selection,
parameter-authority, regression or hash violation was found. The existing BR2
result is `READY_FOR_FAST_FORWARD_TO_MAIN`.
