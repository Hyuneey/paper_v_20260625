---
id: TASK-003
title: Implement candidate universe builder and explicit relation mask
status: blocked
depends_on: [TASK-002]
phase_gate: Milestone 2
suggested_branch: task-003-candidate-universe
---

# TASK-003: Candidate Universe Builder

## 1. Goal

Build a deterministic, provenance-aware candidate set `C_i` for every target variable and export an explicit mask that later GDN Top-K selection must obey.

## 2. Architecture context

Subsystem metadata is a soft prior, not a hard scientific conclusion. The candidate universe reduces search cost while allowing normal-data statistical and type-compatible fallback candidates.

## 3. Candidate sources

```text
C_i = C_i_domain ∪ C_i_stat ∪ C_i_fallback
```

- `domain`: same subsystem/stage/equipment or approved general metadata policy,
- `stat`: approved normal-only score such as lagged correlation,
- `fallback`: type-compatible candidates or approved broader search.

Each source is configurable and independently identifiable.

## 4. Inputs

- variable metadata artifact,
- `train_normal` or approved normal-data statistical summary,
- candidate-policy config,
- feature order.

## 5. Required outputs

- candidate-universe artifact,
- source→target allowed-pair table,
- boolean or indexed candidate mask aligned to feature order,
- provenance per pair,
- candidate-count and coverage report,
- explicit empty-target report.

## 6. Required schema

Each pair record must include:

```text
source
target
allowed: true
origins: [domain, stat, fallback]
origin_scores: optional
policy_version
metadata_artifact_id
normal_summary_artifact_id: optional
feature_order_hash
```

## 7. Core rules

1. Exclude `source == target` from candidate relations.
2. Do not use test labels or attack intervals.
3. Do not hard-code final SWaT pairs.
4. Every allowed pair must include at least one origin.
5. Every target must have an explicit status:
   - supported with candidates,
   - unsupported empty set,
   - expanded by configured fallback.
6. Preserve candidate direction.
7. Persist feature-order hash to prevent mask misalignment.

## 8. In scope

- metadata policies,
- one approved normal-only statistical shortlist,
- type-compatible fallback,
- mask creation,
- provenance,
- reports.

## 9. Out of scope

- GDN training,
- relation scoring with test data,
- causal interpretation,
- silent all-to-all fallback.

## 10. Acceptance criteria

1. Deterministic config produces identical candidate artifacts.
2. Self is excluded for every target.
3. Every mask entry maps correctly to source/target names.
4. Every candidate has provenance.
5. Empty targets are not silently ignored.
6. Statistical candidates use only approved normal data.
7. Artifact records source view, sampling period, and upstream IDs.

## 11. Required tests

- same-subsystem policy,
- type-compatible policy,
- statistical top-M policy on synthetic data,
- union/provenance test,
- self-exclusion test,
- mask/name alignment test,
- empty-target policy test,
- determinism test,
- prohibited test-split input test.

## 12. Stop conditions

Stop if fallback policy, statistical metric, or minimum candidate count requires an unapproved research decision.
