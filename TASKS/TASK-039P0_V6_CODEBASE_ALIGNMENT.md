# TASK-039P0: V6 Codebase Alignment Audit and Migration Freeze

## Objective

Audit commit `337769066f62b8f4fcd8e48a9a8f8d3651e3818a` and freeze the
migration from mixed Phase-1/TASK-032 architecture to v6.

This task is static. It changes no behavior under `src/`, `schemas/`, or
`experiments/`; accesses no research dataset or restricted artifact; calls no
provider or Agent; executes no generated rule; and produces no scientific
result.

## Frozen Decisions

- The listed `paperworks.contracts.*_v1` modules are canonical.
- Phase-1 RuleAst planning, DSL, verifier, runtime, and e2e orchestration are
  legacy read-only compatibility.
- Data, metadata, candidate, masked-GDN, relation-profile, and evaluation
  modules require dataset-neutral v2 adapters.
- ARGOS TASK-022 through TASK-038F is frozen reference-only.
- Core construction uses normal evidence; detector-error context is optional.
- Deterministic validity and label-aware utility are separate.
- `T0`, `T1`, `T1-B`, and `T2` share a common experiment contract where
  applicable.
- `no_rule`, `no_op`, and `abstain` are distinct.

Passing status: `passed_v6_codebase_alignment_freeze`.
