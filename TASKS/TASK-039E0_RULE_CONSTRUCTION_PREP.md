# TASK-039E0-PREP: Synthetic Rule-Construction Protocol Skeleton

## Status

`passed_task039e0_rule_construction_protocol_preparation`

## Objective

Prepare a generic, synthetic-only protocol skeleton for a future
rule-construction comparison and its label-free deterministic validity check.
This task freezes comparison structure before real confirmed relations or LLM
outputs are visible. It generates no rule, calls no LLM, runs no Agent, and
grants no validity, Rule v2, runtime, detector, or deployment authority.

## Frozen future inputs

`ConfirmedRelationPrimitiveV1` binds one future confirmed relation to its
identity, source and target, exact directions, exact delay horizon, approved
source-threshold/stability and target-scale references, and fit/confirmation
evidence references. `ApprovedNumericEvidenceBundleV1` carries only approved
hash references and preregistered window-constant references. Main-method
proposal envelopes cannot contain arbitrary numeric literals.

The preparation accepts synthetic fixtures only. It does not consume a real
D2 result, confirmed relation identity, D1/D2 private ledger, HAI value,
provider, or Agent.

## Frozen comparison

- T0 is a deterministic, zero-LLM-call template path.
- T1 is a one-shot constrained proposal path with no verifier feedback.
- T1-B uses independent, feedback-free generations.
- T2 permits only `revise`, `retrieve`, and `no_rule` in a bounded future
  verifier-feedback loop.
- A future concrete call budget must freeze before relation identities and
  proposals are visible. T1-B total generation calls must equal T2 maximum
  total generation calls. T0 remains zero-call and T1 remains one-shot.
- Result-dependent extra generation and hidden scientific retries are
  prohibited. A transport retry requires a separate preregistered policy.

PREP intentionally selects no production call-budget number. Synthetic tests
use a clearly marked fake budget solely to exercise the invariant.

## LLM-direct-number ablation

`LLMDirectNumberAblationPolicyV1` prepares an isolated future comparison in
which an LLM could propose numbers directly. It must match its designated
main comparator's budget, cannot reuse or replace the calibrated-number main
method, is not executed here, and can never grant validity or runtime
authority.

## Deterministic validity boundary

The project-owned verifier skeleton is label-free and uses no LLM
chain-of-thought. It checks the closed proposal schema, allowed identities,
exact confirmed-relation and direction/horizon bindings, approved numeric
references and origin, variable closure, fixed runtime logic, prohibited data
references, deterministic serialization, provenance, and non-authority
claims. Outcomes are `admissible` or `rejected` with bounded machine-readable
reason codes. An admissible preparation envelope is not an accepted canonical
rule and does not authorize runtime use.

Validity is distinct from utility. Any label or utility input is rejected at
the validity boundary. Utility remains a separately authorized future stage.
The future metrics distinguish rule-construction success, `no_rule` rate,
valid-rule rate, runtime abstention rate, and explanation/rule coverage;
`no_rule` is not automatically a system failure.

## Runtime and canonical contracts

Future LLM use is construction-time only. Runtime remains LLM-free and later
governance is required. Rule v1 behavior is unchanged, Rule v2 is not created,
and the schema drafts are deliberately not registered as execution contracts.
The generic decrease-direction envelope does not add decrease support to the
current canonical Rule v1 bridge; any later materialization requires its own
authorized rule-family/version decision.

## Preparation outputs

- lightweight generic preparation contracts and canonical-path adapters;
- an independent deterministic proposal-envelope validity skeleton;
- five unregistered Draft 2020-12 schema drafts;
- clearly synthetic factories and protocol, validity, schema, and boundary
  tests;
- `docs/task_reports/TASK-039E0_PREP_REPORT.md`.

## Non-authority statement

- D2 result consumed: `false`.
- Confirmed real relation identity consumed: `false`.
- HAI accessed: `false`.
- LLM called: `false`.
- Agent run or authorized: `false`.
- Rule v2 created or execution-authorized: `false`.
- Detector/runtime authorized: `false`.
