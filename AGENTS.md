# AGENTS.md

## 1. Project Mission

This repository implements:

> Graph-guided, training-time agentic verified rule construction for
> explainable multivariate time-series anomaly detection.

The v6 architecture has five stages:

1. data readiness and normal relation evidence construction;
2. bounded Rule Construction Agent;
3. deterministic rule validity and separate rule governance;
4. LLM-free verified-rule runtime;
5. detector FN correction and trace-grounded explanation.

The research contribution is verified rule construction and governance, not a
new detector.

## 2. Current V6 Scope

- Primary dataset candidate: **HAI 23.05**.
- Process scope: **P1 Boiler**, frozen by TASK-039BR2 under the preregistered
  normal-only continuous-step feasibility policy.
- Relation family: pairwise `continuous_step_delayed_response_v1` for the HAI
  MVP; canonical Rule v1 remains unchanged.
- Source: reviewed continuous control/actuator command or feedback under the
  bounded continuous-step protocol.
- Target: continuous process sensor.
- Core construction evidence: normal-only.
- Primary rule role: detector false-negative correction.
- FP correction: supplementary and guarded.
- Runtime LLM: prohibited.

SWaT and WADI are future external-validation datasets. They are not blockers
for the first HAI MVP.

Raw HAI, SWaT, WADI, KPI, and other restricted research data is local-only and
untracked. Never upload it to GitHub, CI artifacts, provider prompts, issue
attachments, or reports.

TASK-039A authorizes only the official `icsdataset/hai` repository pinned at
`2a814cebc9a66b06c9e5cd545e2d72e65d383737` and a restricted
`hai-23.05/**` Git-LFS pull. The official checkout and private label-custody
artifact must remain outside this repository. Public provenance may contain
aggregate structural metadata and custody hashes, never raw rows or attack
details.

TASK-039AR additionally authorizes the official Kaggle dataset
`icsdataset/hai-security-dataset` as a selective payload route only. The
pinned Git snapshot and Git-LFS pointers remain authoritative. Metadata must
freeze before payload acquisition, every one of the ten approved files must be
byte-equivalent, and whole-dataset, HAIEnd, and earlier-version downloads are
prohibited.

TASK-039AR passed exact byte equivalence for all ten approved files, and the
resumed TASK-039A provenance audit passed. HAI 23.05 source provenance is
verified.

TASK-039B completed with `blocked_no_feasible_delayed_response_process` after
reading only authorized normal training files. Both P1 and P3 had zero
eligible reviewed, nonconstant binary/discrete control sources. No primary
process, selected view, or authoritative split was frozen.

TASK-039BR0 diagnosed the source mismatch and froze
`versioned_continuous_step_delayed_response_on_HAI` as the recovery route. Its
result remains source-morphology readiness only.

TASK-039BR1 completed the protocol freeze for
`continuous_step_delayed_response_v1`. It grants no rule, verifier, runtime,
or process-selection authority and accessed no real HAI values. Rule v1 is
unchanged and Rule v2 remains a migration plan.

TASK-039BR2 executed that frozen protocol on verified normal train1-train3
data. P1 alone passed the feasibility gate and is frozen as the selected
process; P3 remained infeasible. TASK-039C is authorized for P1
candidate-universe and graph-evidence work only. It has no Rule v2, rule,
verifier, runtime, Agent, detector, outer, or sealed authority.

TASK-039C completed with
`passed_task039c_three_arm_candidate_cohort_freeze`. META, STAT, and the
compatibility-closed upstream-aligned GDN arm were independently audited and
integrated as the unscored union of their top-20 views. The final P1 Boiler
profiling cohort contains 47 unique directed pairs with complete arm-local
provenance, no merged score, and no global scientific rank. TASK-039D0 protocol
design is authorized next; real TASK-039D profiling and all train3/train4/test,
label, attack, Rule v2, Agent, detector/runtime, outer, and sealed execution
remain unauthorized.

## 3. Canonical, Legacy, and Reference Paths

### Canonical scientific contracts

The authoritative path is `src/paperworks/contracts/`, specifically:

- `rule_v1.py`
- `graph_v1.py`
- `evidence_v1.py`, retained only for its original scope
- `parameter_v1.py`
- `verifier_v1.py`
- `runtime_authority.py`
- `runtime_v1.py`
- `explanation_v1.py`
- `context_protocol_v1.py`
- `normal_evidence_binding_v1.py`
- `canonical_collection_v1.py`
- `outcome_binding_v1.py`

New v6 work must extend or adapt this contract path. Do not create a competing
RuleAst authority.

TASK-039P1C binds P1B evidence and outcomes into this path. Evidence,
construction, governance, verifier acceptance, runtime authorization, and
deployment receipts remain separate authority layers. The v6 delayed-response
bridge supports increase relations only; decrease support remains a future
rule-family or version decision.

### Reusable producers

Reuse through explicit v2 adapters:

- `src/paperworks/data/*`
- `src/paperworks/metadata/*`
- `src/paperworks/candidates/*`
- `src/paperworks/gdn/masked.py`
- selected `gdn/torch_backend.py` code only after fidelity approval
- selected `profiling/relations.py` code

Current SWaT defaults and split semantics are not canonical HAI contracts.

### Legacy read-only compatibility

The following paths remain importable for historical tests and artifacts but
must not be dependencies of future HAI/v6 modules:

- `src/paperworks/dsl/*`
- `src/paperworks/verification/*`
- `src/paperworks/runtime/*`
- `src/paperworks/planning/refiner.py`
- legacy template/LLM planners that produce `RuleAst`
- historical `src/paperworks/e2e/*` orchestration

Do not delete, rename, warn, reformat, or behaviorally modify these paths
without an explicit compatibility task.

### Frozen reference track

`experiments/argos_reproduction/*` and TASK-022 through TASK-038F are frozen
reference-only. ARGOS is classified as `partial_methodological_support`.

Do not:

- tune ARGOS prompts or models on its exposed outer partition;
- create a branch or detector winner;
- modify historical reports, configs, metrics, rules, or predictions;
- continue ARGOS execution without a new explicit authorization.

## 4. Scientific Separations

### Rule validity

Deterministic validity covers:

- structural correctness;
- source/target compatibility;
- graph/evidence binding;
- parameter provenance;
- split compliance;
- operational contract;
- claim boundary.

### Rule utility

Label-aware utility covers:

- normal false-fire;
- inner attack coverage;
- detector FN recovery;
- added false positives;
- duplicate firing;
- no-op-aware selection.

Attack-label performance must not decide deterministic validity acceptance.
Validity and utility artifacts, statuses, and tests must remain separate.

### Evidence types

Core construction requires a new normal-only `NormalRelationEvidence` contract
containing support, response direction, lag/magnitude summaries, stability,
operating regime, matched normal references, and parameter references.

Optional `DetectorErrorContext` may contain authorized development/inner FN or
FP context and detector prediction references. It cannot replace or mutate
normal relation evidence.

The anomaly-anchored `EvidencePackageV1` remains valid only for its original
scope. Do not silently reinterpret it as the v6 normal-only input.

### Outcome states

- `no_rule`: construction terminates because evidence is insufficient.
- `no_op`: a valid rule exists but governance does not select it.
- `abstain`: an authorized rule cannot evaluate the runtime window.

Provider failure, invalid JSON, verifier rejection, and budget exhaustion are
explicit failures, not `no_rule`.

## 5. Agentic Comparison

Freeze these future arms:

- `T0`: deterministic template construction.
- `T1`: one-shot constrained LLM construction.
- `T1-B`: independent generations using the same total provider-call budget
  as T2, without verifier feedback.
- `T2`: bounded verifier-feedback construction with
  `revise`/`retrieve`/`no_rule`.

Where scientifically applicable, use the same candidate, evidence, parameter
strategy, DSL, verifier, model/provider policy, and total call budget.

An LLM may propose only structured, bounded contract data. It may not:

- invent variables outside the candidate;
- author uncontrolled numeric parameters;
- approve its own output;
- receive outer or sealed-test feedback;
- execute at runtime.

## 6. Data and Split Governance

Split the raw timeline before windowing. Purge boundary context by at least
`window_size - 1`, plus required lag.

V6 must define dataset-neutral roles for:

- normal candidate learning;
- normal relation profiling and calibration;
- deterministic validity;
- label-aware inner utility;
- one-way outer validation;
- sealed evaluation.

Every API must validate its permitted split role. Outer data cannot select,
tune, repair, revise, or govern a rule. Sealed data is evaluation-only after
preregistration and explicit approval.

For HAI, store locally:

- source and edition;
- local filenames and SHA-256 hashes;
- feature names hash and types;
- timestamp, sampling, labels, and encoding;
- preprocessing;
- terms acknowledgement;
- manifest and split schema versions.

If an edition or field is unknown, record `unverified`; do not infer it.

## 7. Candidate and GDN Policy

GDN edges are candidate or predictive relations, never causes or root causes.

Candidate extraction must:

1. apply the approved candidate mask before Top-K;
2. exclude persisted self-relations;
3. handle empty sets;
4. distinguish candidate edges from message-passing self-loops;
5. assert every exported edge belongs to the candidate universe.

TASK-039P1D freezes the current GDN import and claim boundary:

- `paperworks.gdn.masked` is a project-owned masked candidate-extraction
  component, not a complete GDN model;
- the deterministic and Torch/PyG trainers are synthetic smoke-only backends;
- only an `upstream_aligned_validated` backend may be called GDN in a future
  RQ1 experiment;
- the production graph-ranking backend remains open until TASK-039A/B establish
  HAI schema and process feasibility.

Torch and Torch Geometric are optional dependencies. Lightweight package
imports must remain usable without them, and optional backend access must fail
through the project-owned dependency error.

## 8. Rule, Verifier, Governance, and Runtime

Numeric parameters must reference deterministic normal-data calibration
artifacts. Rule validity must be machine-readable and deterministic.

Accepted runtime rules require:

- graph and evidence binding;
- parameter provenance;
- accepted verifier result;
- immutable rule hash;
- explicit runtime authority.

Runtime is LLM-free. Do not execute generated Python through `exec`, `eval`,
`compile`, dynamic import, subprocess Python files, or host callbacks.

Explanations must bind to observed runtime facts, satisfaction traces, parameter
references, and provenance. Do not claim causality.

FP correction is supplementary. It requires:

- FP removal evidence;
- frozen TP-removal guard;
- zero or frozen true-event-removal guard;
- non-regression policy;
- cross-split directional stability;
- mandatory no-op candidate.

## 9. Provider and Privacy

- Use a provider interface and mock provider in tests.
- External calls are forbidden in CI.
- Secrets come from environment variables or approved secret stores.
- Prompts contain structured aggregate evidence, not raw time-series rows,
  private paths, credentials, outer data, or sealed data.
- Record model, provider, template hash, evidence hash, response hash, token
  usage, and redaction status.
- Every real call requires an exact, precommitted budget and receipt-first
  one-call enforcement.

## 10. Reproducibility

Every scientific artifact records:

- schema and artifact version;
- dataset and split manifest IDs;
- source view and sampling period;
- data fingerprint;
- config hash;
- code commit;
- upstream revisions;
- random seed;
- creation timestamp;
- upstream artifact IDs.

Do not hard-code HAI, SWaT, WADI, or KPI scientific conclusions in library
logic.

## 11. Coding and Testing

- Use type hints for public APIs.
- Validate external inputs at module boundaries.
- Separate pure computation from I/O.
- Keep scientific choices in versioned configs.
- Unit and CI tests use synthetic fixtures only.
- Add negative tests for leakage, masks, types, authority, and prohibited LLM
  behavior.
- Never delete, skip, or weaken a relevant test to pass a task.
- Do not import optional torch modules during static inventory work.

## 12. Work Discipline

Before coding:

1. read this file and the active task;
2. verify branch, HEAD, origin equality, and worktree state;
3. inspect existing contracts, tests, configs, and open decisions;
4. confirm required local data without copying it;
5. identify claim, split, and artifact boundaries.

Before completion:

1. run applicable tests, compile, JSON, self-hash, dependency, diff, and safety
   checks;
2. verify no restricted data or private artifact entered Git;
3. verify historical frozen paths remain unchanged;
4. document optional dependency boundaries exactly;
5. commit and push only a complete, verified task when the task requires it.

## 13. Stop Conditions

Stop and record the issue when:

- required data, schema, lineage, or private hash is unavailable;
- implementation would require outer/test feedback or data leakage;
- a scientific choice has multiple material alternatives;
- GDN fidelity, detector identity, or Rule v2 scope is required but unresolved;
- raw data would enter Git or an external provider;
- generated code would need host execution;
- a requested change would modify frozen ARGOS or legacy compatibility
  behavior without explicit authorization.
