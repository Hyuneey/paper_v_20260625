# V6 Migration Matrix

| Current path | Classification | V6 action |
|---|---|---|
| Listed contract v1 modules | `canonical_v6_core` | Preserve authority; decouple Phase-1 adapters in P1. |
| `data/*`, `metadata/*` | `reusable_with_v2_adapter` | Add dataset-neutral HAI provenance and split contracts. |
| `candidates/universe.py`, `gdn/masked.py` | `reusable_with_v2_adapter` | Bind masking and candidate semantics to v2 artifacts. |
| `gdn/torch_backend.py` | `unresolved_research_decision` | Complete fidelity and optional-import audit. |
| `profiling/relations.py`, `evaluation/harness.py` | `reusable_with_v2_adapter` | Remove dataset defaults and separate validity/utility/evaluation. |
| Phase-1 DSL/verifier/runtime/RuleAst/e2e | `legacy_read_only` | Historical compatibility only. |
| ARGOS reference track | `frozen_reference_only` | No new execution, tuning, or reinterpretation. |

## Migration Order

1. TASK-039P1: dataset-neutral foundations, evidence, outcomes, and adapters.
2. TASK-039A: official HAI source and provenance audit.
3. TASK-039B: P1/P3 normal-only feasibility and one-process freeze.
4. TASK-039C onward: candidates, profiles, construction, governance, detector,
   explanation, outer freeze, and sealed execution.

Machine-readable matrix:
`docs/task_reports/TASK-039P0_MIGRATION_MATRIX.json`.
