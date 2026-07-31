# V6 Implementation Plan

## Objective

Build a project-owned method for graph-guided, training-time agentic verified
rule construction in multivariate CPS anomaly detection.

```text
local HAI 23.05 candidate data
-> dataset-neutral provenance and leakage-safe splits
-> one-process feasibility freeze
-> masked candidate relations
-> normal-only delayed-response evidence
-> bounded T0/T1/T1-B/T2 construction
-> deterministic validity
-> separate no-op-aware utility governance
-> LLM-free runtime
-> detector FN correction
-> trace-grounded explanation
-> one-way outer and one-time sealed evaluation
```

HAI is a candidate until TASK-039A/B establish provenance and feasibility.
SWaT and WADI remain future external validation and are not blockers.

## TASK-039P0: Codebase Alignment

Freeze the AST module/public-symbol inventory, canonical and legacy boundaries,
scientific separations, open decisions, and source migration order without
changing scientific behavior or accessing research data.

## TASK-039P1: Canonical Foundation Migration

Implement:

- dataset-neutral manifest and split v2 contracts;
- `NormalRelationEvidence`;
- optional `DetectorErrorContext`;
- validity/utility artifact separation;
- typed `no_rule`, `no_op`, and `abstain`;
- v1 compatibility adapters;
- removal of canonical dependence on Phase-1 adapters;
- GDN fidelity and optional-import decision support.

Do not load HAI merely to implement schemas and adapters.

## TASK-039A: HAI Source and Provenance

Audit official HAI 23.05 edition, terms, files, hashes, timestamps, sampling,
features, labels, local-only storage, and reproducible manifest. Commit no raw
rows or windows.

## TASK-039B: P1/P3 Feasibility and Process Freeze

Using authorized normal data only, type control and sensor variables, audit
P1/P3 support, test delayed-response feasibility, and freeze exactly one
process plus canonical and optional GDN views.

## TASK-039C Onward

1. TASK-039C: candidate-universe and graph evidence construction.
2. TASK-039D: normal relation profiling and deterministic calibration.
3. TASK-039E: T0 deterministic template baseline.
4. TASK-039F: common T1/T1-B/T2 bounded construction protocol.
5. TASK-039G: deterministic validity and no-op-aware utility governance.
6. TASK-039H: primary detector and FN-correction protocol.
7. TASK-039I: LLM-free runtime and trace-grounded explanation.
8. TASK-039J: outer prediction freeze and one-way validation.
9. TASK-039K: joint sealed-test preregistration.
10. TASK-039L: one-time sealed execution after explicit approval.

## Construction Arms

- `T0`: deterministic template construction.
- `T1`: one-shot constrained LLM construction.
- `T1-B`: independent generations with T2's total call budget and no feedback.
- `T2`: bounded verifier-feedback `revise`/`retrieve`/`no_rule`.

Where applicable, all arms share candidates, evidence, parameter strategy, DSL,
verifier, model/provider policy, and total call budget. Generated Python is
prohibited.

## Global Gates

Every task must preserve split-before-windowing and sealed isolation, keep raw
data and private artifacts untracked, distinguish validity from utility and
runtime outcomes, retain unsupported cases, use synthetic CI fixtures, and
record configs, hashes, commits, seeds, and environments.

ARGOS is frozen reference-only after TASK-038F. GDN remains a pinned
architecture reference pending fidelity audit. Neither reference silently
defines v6 splits, evaluation, rule authority, or runtime policy.
