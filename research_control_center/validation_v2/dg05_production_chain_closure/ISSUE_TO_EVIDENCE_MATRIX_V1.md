# DG-05 Production Chain Issue-to-Evidence Matrix V1

Status: `DECISION_REQUIRED / NO_GO_FOR_REAL_DG05_ACCESS`
Real attack/test/label/scenario accesses: `0`

This matrix classifies the PRE-DG05 audit findings before implementation. It does not grant DG-05 access and does not reinterpret missing evidence as zero.

| Class | Count | Meaning |
|---|---:|---|
| `ENGINEERING_DEFECT` | 8 | The frozen scientific meaning is sufficiently explicit; implementation may close the path without a new scientific choice. |
| `SCIENTIFIC_BINDING_AMBIGUITY` | 4 | More than one scientifically meaningful behavior remains possible; code must reject production execution until one user-approved binding is frozen. |
| `BLOCKED_EVIDENCE` | 1 | The required method-specific source bytes/receipts are not represented by the current public authority set. |
| `APPROVAL_GATE` | 1 | Fresh approval is intentionally absent and is not a code defect. |

The detailed, machine-readable rows are in `ISSUE_TO_EVIDENCE_MATRIX_V1.csv`. The audit record in `pre_dg05_state_audit/` remains byte-identical and retains its `NO_GO` verdict.

## Decisions that are already determined

- Multiple disjoint intervals remain one official scenario.
- A primary scenario is a hit when a frozen alarm overlaps any authorized interval in the same physical file.
- The scenario contributes at most one primary hit; it is not split and its intervals are not replaced by one bounding interval.
- Scenario interval endpoints do not need to equal sampled timestamp strings; inclusive datetime overlap is authoritative.
- Missing runtime or normal-burden evidence is not zero.

## Decisions that remain open

- Detection-delay anchoring for a hit in a later disjoint interval.
- Duplicate timestamp handling across projection, prediction, scenarios, runtime windows, and metrics.
- Gap handling and the relation between row offsets and elapsed seconds.
- The exact public meaning of “participating Rule/source” in the runtime census.

These items are consolidated in `SCENARIO_TIME_RUNTIME_BINDING_DECISION_BRIEF_V1.md` rather than fragmented into separate gates.

## Closure state

Prospective, tested implementations now exist for exact release-root replay, fresh-process multi-source custody, plural-interval primary overlap, strict runtime census, source-derived normal burden, and upstream primitive reconstruction. They are not labeled as the final production route: the plural-delay/time/participation choices remain unapproved, the complete normal-burden source registry is not demonstrated, and the final projection-to-result orchestrator has therefore not been frozen or approved.
