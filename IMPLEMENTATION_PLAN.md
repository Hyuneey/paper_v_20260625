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
resumed. TASK-039B is next; no process has yet been selected.

## TASK-039B: P1/P3 Feasibility and Process Freeze

Using authorized normal data only, type control and sensor variables, audit
P1/P3 support, test delayed-response feasibility, and freeze exactly one
process plus canonical and optional GDN views.

Status: blocked with `blocked_no_feasible_delayed_response_process`. P1 and P3
both had zero eligible reviewed, nonconstant binary/discrete source variables
under the frozen first-MVP policy. No process, selected view, or authoritative
split was frozen. Train4 remained an unread normal guard and the official graph
was non-scoring.

## TASK-039C Onward

TASK-039C is not authorized until a new researcher-approved task resolves the
source/process feasibility contradiction without retroactively lowering the
TASK-039B gates.

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

ARGOS is frozen reference-only after TASK-038F. The current GDN trainers are
synthetic smoke-only; the exact production graph-ranking backend remains open
until HAI feasibility evidence exists. Neither reference silently defines v6
splits, evaluation, rule authority, or runtime policy.
