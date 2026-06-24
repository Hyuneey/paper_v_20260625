---
id: TASK-005
title: Run pre-registered candidate feasibility kill-test
status: blocked
depends_on: [TASK-004]
phase_gate: Phase Gate A
suggested_branch: task-005-candidate-kill-test
---

# TASK-005: Candidate Discovery Feasibility Kill-Test

## 1. Goal

Evaluate whether masked GDN candidate extraction produces stable and scientifically useful candidate pairs before relation profiling work begins.

## 2. Architecture context

If candidate discovery is unstable or fails to recover pre-registered plausible relations, downstream rule construction is not justified. This is a kill-test, not a performance showcase.

## 3. Ground-reference policy

Known relation pairs used for evaluation must be pre-registered from:

- process documentation,
- dataset documentation,
- an independently prepared metadata relation list,
- or a clearly labeled expert list created before viewing candidate outputs.

Do not construct the reference set from final test attack outcomes or post-hoc successful candidates.

## 4. Inputs

- candidate-edge artifacts across approved K values and seeds,
- CandidateUniverse artifacts,
- pre-registered reference relation set,
- metadata.

No final test labels are permitted.

## 5. Required analyses

- Recall@K against the pre-registered relation set,
- per-target candidate coverage,
- edge frequency across seeds,
- edge persistence across K,
- candidate-origin distribution,
- unsupported/empty targets,
- sensitivity to domain/stat/fallback candidate sources,
- failure cases.

## 6. Required outputs

- machine-readable metrics,
- stability table,
- all evaluated candidates, not only successes,
- negative-result section,
- artifact provenance index,
- explicit Phase Gate A recommendation:
  - proceed,
  - revise candidate discovery,
  - stop current architecture.

## 7. Acceptance criteria

1. Evaluation reference is documented and pre-registered.
2. Results include every configured seed and K.
3. No threshold is selected using final test data.
4. No successful pair is cherry-picked without reporting selection criteria.
5. Candidate artifacts are traceable to masks, checkpoints, views, and manifests.
6. Gate recommendation is explicit and evidence-based.

A numerical pass threshold must not be invented by Codex. If none is approved, report results and request a decision.

## 8. Required tests

- metric fixture,
- stability-frequency fixture,
- reference-set provenance validation,
- deterministic report generation,
- missing-run detection,
- no-test-role guard.

## 9. Stop condition

Do not start TASK-006 until Phase Gate A is reviewed and approved.
