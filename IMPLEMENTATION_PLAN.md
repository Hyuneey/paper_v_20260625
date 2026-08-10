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

TASK-039P1 is decomposed and complete:

1. **TASK-039P1A: data and split foundation**
   - Status: completed.
   - dataset-neutral manifest/view/split v2 contracts;
   - explicit v6 role permissions;
   - purge and split-before-windowing enforcement;
   - v1 data adapters and independent v2 schemas.
2. **TASK-039P1B: evidence and construction outcomes**
   - Status: completed.
   - `NormalRelationEvidence`;
   - optional `DetectorErrorContext`;
   - validity/utility separation;
   - typed `no_rule`, `no_op`, and `abstain`.
3. **TASK-039P1C: canonical collection and decoupling**
   - Status: completed.
   - explicit `EVID-V6-*` and `NREF-V6-*` bindings;
   - dataset-neutral canonical delayed-response collection;
   - verifier/runtime collection protocol and normalized evidence boundary;
   - legacy TASK-032 hash-compatible collection adapter;
   - separate construction, governance, and synthetic deployment receipts.
4. **TASK-039P1D: GDN import and fidelity support**
   - Status: completed.
   - Torch/PyG optional-import boundary and stable dependency error;
   - exact pinned-source fidelity mapping;
   - current trainers frozen as smoke-only and masked extraction frozen as a
     reusable component, not a complete GDN backend.

P1A, P1B, P1C, P1D, and parent TASK-039P1 are complete. TASK-039AR and the
resumed TASK-039A audit also passed. HAI source provenance is verified, but
process feasibility and the production GDN backend remain unresolved.

## TASK-039A: HAI Source and Provenance

Audit official HAI 23.05 edition, terms, files, hashes, timestamps, sampling,
features, labels, local-only storage, and reproducible manifest. Commit no raw
rows or windows.

Status: completed with `passed_hai_2305_official_provenance_audit`.

TASK-039AR passed `passed_official_distribution_byte_equivalence` using only
selective file delivery from the official `icsdataset` Kaggle distribution.
All ten payloads matched the pinned Git-LFS hashes and sizes before TASK-039A
resumed. TASK-039B subsequently blocked under its discrete-source policy;
TASK-039BR2 later selected P1 under the separately preregistered continuous-step
protocol.

## TASK-039B: P1/P3 Feasibility and Process Freeze

Using authorized normal data only, type control and sensor variables, audit
P1/P3 support, test delayed-response feasibility, and freeze exactly one
process plus canonical and optional GDN views.

Status: `blocked_no_feasible_delayed_response_process`. Both processes had
zero eligible reviewed, nonconstant binary/discrete sources. No process, view,
or authoritative split was frozen.

## TASK-039BR0/BR1/BR2: Relation-Family Recovery

TASK-039BR0 completed the source root-cause audit and selected
`versioned_continuous_step_delayed_response_on_HAI`. The finding is structural
source-morphology readiness only and does not select P1 or P3.

TASK-039BR1 completed the preregistration of the second bounded
`continuous_step_delayed_response_v1` family, fit-only source/target scale
rules, normal-only support gates, process Pareto policy, and additive migration
plans. Rule v1, Verifier v1, and Runtime v1 remain unchanged; Rule v2 was not
created.

TASK-039BR2 completed with
`passed_hai_2305_continuous_step_single_process_freeze`. It used authorized
normal train1-3 values, preserved train4/test/label/summary/custody boundaries,
and selected P1 because P1 alone passed the frozen gate. Rule v1 remains
unchanged and Rule v2 was not created.

## TASK-039C Onward

TASK-039C0 completed the P1 candidate-discovery protocol freeze. It binds one
12-source, 12-target, 144-pair directed universe and top-10/20/40 budgets for
META, STAT, and upstream-aligned GDN arms. META is value-free; STAT and GDN
may use P1 train1/train2 only. BR2 pair-level outcomes are prohibited as
candidate supervision. Integration is an unscored union with provenance.

The parallel META, STAT, GDN, review, and integration branches start from the
exact same C0 commit. The GDN arm must pass its upstream fidelity receipt and
cannot substitute a smoke backend. TASK-039D remains unauthorized until the
candidate arms are independently completed and integrated.

1. TASK-039C-META/STAT/GDN: parallel candidate discovery.
2. TASK-039C-INTEGRATE: unscored candidate-set union with provenance.
3. TASK-039D: normal relation profiling and deterministic calibration.
4. TASK-039E: T0 deterministic template baseline.
5. TASK-039F: common T1/T1-B/T2 bounded construction protocol.
6. TASK-039G: deterministic validity and no-op-aware utility governance.
7. TASK-039H: primary detector and FN-correction protocol.
8. TASK-039I: LLM-free runtime and trace-grounded explanation.
9. TASK-039J: outer prediction freeze and one-way validation.
10. TASK-039K: joint sealed-test preregistration.
11. TASK-039L: one-time sealed execution after explicit approval.

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

ARGOS is frozen reference-only after TASK-038F. The current GDN trainers are
synthetic smoke-only; the exact production graph-ranking backend remains open
until HAI feasibility evidence exists. Neither reference silently defines v6
splits, evaluation, rule authority, or runtime policy.
