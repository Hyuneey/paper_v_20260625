---
id: TASK-005
title: Run pre-registered candidate feasibility smoke test
status: complete
depends_on: [TASK-004]
phase_gate: Phase Gate A
suggested_branch: task-005-candidate-kill-test
---

# TASK-005: Candidate Discovery Feasibility Smoke Test

## 1. Goal

Verify that the candidate-universe and masked GDN extraction pipeline produces reproducible, provenance-rich candidate artifacts without mask violations or test-label leakage.

## 2. Architecture context

This is a smoke feasibility check, not a benchmark evaluation and not evidence of final detection or explanation performance.

The TASK-005 report must state:

- "This is a smoke feasibility result."
- "This is not a final performance claim."
- "This does not validate anomaly detection performance."

## 3. Ground-reference policy

No benchmark-style relation recall or strict relation checklist coverage is required for TASK-005. If known relation pairs are inspected later, they must be pre-registered from:

- process documentation,
- dataset documentation,
- an independently prepared metadata relation list,
- or a clearly labeled expert list created before viewing candidate outputs.

Do not construct the reference set from final test attack outcomes or post-hoc successful candidates.

## 4. Inputs

- `configs/candidates/task005_metadata_same_stage_only_smoke.json`,
- candidate-edge artifacts from the approved smoke config,
- CandidateUniverse artifacts,
- metadata.

No final test labels are permitted.

## 5. Required analyses

- candidate artifact generation success,
- mask membership for every exported candidate edge,
- self-edge exclusion,
- message-passing self-loop separation,
- same-config/same-seed hash stability,
- required provenance-field completeness,
- per-target candidate coverage,
- candidate-origin distribution,
- unsupported/empty targets.

## 6. Required outputs

- machine-readable smoke report,
- all emitted candidates,
- negative-result section,
- artifact provenance index,
- explicit Phase Gate A recommendation:
  - proceed,
  - revise candidate discovery,
  - stop current architecture.

## 7. Acceptance criteria

1. Candidate artifacts are generated successfully from the approved configuration.
2. Every exported GDN candidate edge belongs to the precomputed CandidateUniverse `C_i`.
3. No self-edge is exported as a candidate relation.
4. Message-passing self-loops, if used internally, are not persisted as relation candidates.
5. The same config and seed produce identical or hash-stable candidate artifacts.
6. Required provenance fields are present:
   - candidate origin,
   - source variable,
   - target variable,
   - rank,
   - score, if available,
   - seed,
   - K,
   - config hash,
   - data manifest reference.
7. No sealed test labels or attack labels are used for candidate generation, filtering, thresholding, or pass/fail decisions.
8. Candidate origins match `metadata_same_stage_only_smoke`.

Seed/K stability may be logged descriptively, but it is not a pass/fail gate in TASK-005.

Out of scope:

- benchmark-style candidate recall,
- final SWaT attack-variable coverage,
- strict relation checklist coverage,
- point-adjusted or detection metrics,
- K tuning based on observed smoke results,
- enabling fallback candidates after seeing results.

## 8. Required tests

- smoke-report fixture,
- provenance completeness fixture,
- deterministic report generation,
- missing-run detection,
- no-test-role guard.

## 9. Stop condition

Do not start TASK-006 until Phase Gate A is reviewed and approved.
