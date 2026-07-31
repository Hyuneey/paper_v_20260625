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

Canonical verifier and runtime-authority modules currently depend on
`contracts.phase1_adapters`. TASK-039P1 must replace that dependency through a
dataset-neutral artifact boundary without changing historical behavior.

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

No arm is executed in TASK-039P0.
