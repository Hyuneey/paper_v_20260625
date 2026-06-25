# Candidate Universe

TASK-003 implements deterministic candidate-universe construction under `src/paperworks/candidates`.

## Purpose

The candidate universe defines the allowed directed source-target pairs `C_i` for every target variable. TASK-004 GDN extraction must apply this mask before Top-K relation selection.

Candidate edges are predictive candidates only. They are not causal claims or physical ground truth.

## Implemented modules

- `paperworks.candidates.CandidatePolicy`
- `paperworks.candidates.CandidatePair`
- `paperworks.candidates.CandidateUniverseArtifact`
- `paperworks.candidates.build_candidate_universe()`
- `paperworks.candidates.candidate_mask()`
- `paperworks.candidates.indexed_candidates_by_target()`

`CandidatePolicy.from_dict()` loads the project JSON policy shape used by `configs/candidates/swat_candidate_policy.json`.

## Mask contract

The boolean mask is target-major:

```python
mask[target_index][source_index]
```

Indexes are aligned to `CandidateUniverseArtifact.feature_order`. The artifact stores `feature_order_hash`, and every pair repeats that hash to prevent silent mask/name misalignment.

Self-edges are prohibited in persisted candidate relations. Message-passing self-loops, if needed later by GDN internals, must remain separate from this artifact.

## Candidate origins

`C_i = C_i_domain union C_i_stat union C_i_fallback`

Implemented origins:

- `domain`: same stage or same subsystem, subject to type compatibility.
- `stat`: absolute lagged Pearson shortlist from approved normal-only data.
- `fallback`: explicit type-compatible expansion to a configured minimum count.

Every allowed pair records at least one origin. If multiple mechanisms select the same pair, origins are merged.

## Type policy

The default policy matches the current milestone scope:

- source: binary actuator
- target: continuous sensor

This supports the initial actuator-to-sensor relation class without hard-coding SWaT relation pairs.

## Split and leakage guard

`build_candidate_universe()` requires a `SplitManifest` permitted for `train_candidate_learner`. Passing `test` or other prohibited split roles is rejected.

Statistical candidates require:

- `SplitRole.TRAIN_NORMAL`,
- explicit `normal_data`,
- equal-length normal series for all features,
- an optional `normal_summary_artifact_id` when the caller has a persisted summary.

No attack labels, test intervals, or validation outcomes are used by this module.

## Default SWaT policy

`configs/candidates/swat_candidate_policy.json` enables metadata same-stage candidates only:

- `domain_same_stage: true`
- `statistical_top_m: 0`
- `fallback_min_candidates_per_target: 0`

Statistical and fallback paths are implemented and tested with synthetic fixtures, but the default SWaT policy leaves them disabled until a later task explicitly approves a smoke-run policy.

## Target status

Every target receives an explicit status:

- `supported_with_candidates`
- `unsupported_empty_set`
- `expanded_by_configured_fallback`

Empty targets are also listed in `empty_targets`; they are not silently ignored.

## Test coverage

`tests/test_candidate_universe.py` covers:

- same-stage domain policy,
- type-compatible fallback,
- statistical Top-M on synthetic normal data,
- union/provenance merging,
- self-edge exclusion,
- target-major mask/name alignment,
- explicit empty-target reporting,
- deterministic artifact IDs,
- prohibited test split input,
- missing normal data rejection.
