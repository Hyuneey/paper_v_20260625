# V6 Canonical Architecture

## Research Architecture

V6 freezes five stages:

1. data readiness and normal relation evidence construction;
2. bounded Rule Construction Agent;
3. deterministic rule validity and separate rule governance;
4. LLM-free verified-rule runtime;
5. detector false-negative correction and trace-grounded explanation.

The first MVP candidate is HAI 23.05. Exactly one process is selected only
after P1/P3 feasibility. The first relation family is pairwise delayed response
from a binary or normalized discrete control signal to a continuous sensor.

Core construction is normal-only. Detector FN correction is primary. FP
correction is supplementary and requires true-positive and event safeguards.

## Canonical Contracts

- `paperworks.contracts.rule_v1`
- `paperworks.contracts.graph_v1`
- `paperworks.contracts.evidence_v1`, original scope only
- `paperworks.contracts.parameter_v1`
- `paperworks.contracts.verifier_v1`
- `paperworks.contracts.runtime_authority`
- `paperworks.contracts.runtime_v1`
- `paperworks.contracts.explanation_v1`

`EvidencePackageV1` remains anomaly/event-anchored. It must not be silently
reused as `NormalRelationEvidence`.

TASK-039P1B adds a lightweight `paperworks.v6` foundation for normal evidence,
optional detector context, construction/governance outcomes, and runtime
disposition projection. TASK-039P1C binds these artifacts through
`paperworks.contracts` without creating a competing Rule DSL or verifier.
The canonical verifier and runtime-authority modules now consume a bounded
collection protocol rather than the concrete Phase-1 collection.

The canonical v6 context contains dataset/view/split v2 manifests, normal
evidence, explicit Rule v1 evidence and normal-reference bindings, the graph,
and approved parameters. Evidence and construction grant no authority.
Deployment requires accepted validity, a selected-rule governance receipt,
and synthetic-only runtime authorization. The first bridge supports increase
relations only; decrease remains explicitly unsupported.

## Reusable, Legacy, and Frozen Paths

Data, metadata, candidate-universe, masked-GDN, relation-profile, and evaluation
logic are reusable only through v2 adapters. `gdn.torch_backend` remains
unresolved pending source-fidelity and optional-import evidence.

Phase-1 DSL, verifier, runtime, RuleAst planning, and historical e2e
orchestration are legacy read-only. Future HAI/v6 modules cannot depend on
them.

ARGOS reproduction code and TASK-022 through TASK-038F are a frozen reference
track with `partial_methodological_support`.

## Construction Arms

- `T0`: deterministic template construction.
- `T1`: one-shot constrained LLM construction.
- `T1-B`: independent budget-matched generations without verifier feedback.
- `T2`: bounded verifier-feedback with `revise`, `retrieve`, and `no_rule`.

No construction arm is executed by the P1A/P1B foundation tasks.
