# ARGOS Reproduction Audit and Paper-Code Alignment Protocol

TASK-022 is an audit/protocol task only. It does not approve real LLM calls, execution of LLM-generated Python, full ARGOS experiments, or changes to the paperworks proposed-method pipeline.

## Purpose

This protocol separates ARGOS reproduction from the existing multivariate
extension infrastructure built in TASK-000 through TASK-021. The current
`paperworks` pipeline remains feasibility infrastructure for the proposed
multivariate extension. It is not an ARGOS reproduction.

The required research sequence is:

1. reproduce ARGOS rule generation;
2. compare rule-only, detector-only, and detector-plus-rule behavior;
3. determine why ARGOS uses rules as a detector complement;
4. transfer univariate ARGOS to SWaT;
5. extend to multivariate temporal relation rules.

## Evidence Base

| Source | Status | Notes |
|---|---|---|
| ARGOS paper | inspected | `https://arxiv.org/abs/2501.14170`, v1 submitted 2025-01-24. |
| ARGOS local reference | inspected read-only | `external/argos` at `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`. |
| ARGOS license | inspected | MIT license in `external/argos/LICENSE`. |
| Current research repo | inspected | TASK-022 starts from `5ce6647`. |

Historical README blobs were not fully inspected because the local ARGOS clone
is a partial `--filter=blob:none` clone and older README blobs require a remote
fetch. Network escalation was not requested for TASK-022 because the task is a
local audit/protocol task.

## Paper Workflow to Reproduce

The ARGOS paper describes:

- training-time LLM rule generation rather than runtime LLM inference;
- a Detection Agent, Repair Agent, and Review Agent feedback loop;
- executable anomaly rules as the intermediate representation;
- top-k rule selection to improve training efficiency;
- detector-plus-rule aggregation, where rules are trained from false negatives
  and false positives of a selected base detector;
- Event-PA F1 as ARGOS paper's primary reported metric.

For this project, Event-PA and test-set behavior may be reproduced only inside
an explicitly labeled ARGOS reproduction sandbox. They must not become the
default metric or split policy for the multivariate extension.

## Current Code Audit

Pinned ARGOS commit:

```text
6b24161ff08de069840a1fb4fbaecf7bf8e393f1
```

Current README documents these training modes:

- `train-LLM-only`
- `train-LLM-only-parallel`
- `train-evolution`

Current code still exposes detector-plus-rule related modes and paths:

- `driver.py` accepts `train-combined-fn`, `train-combined-fp`, and
  `eval-combined`.
- `common/common.py` implements `combine_labels`:
  - false-negative compensation uses `np.maximum(model_labels, rule_labels)`;
  - false-positive compensation uses `np.minimum(model_labels, rule_labels)`.
- `datasets/dataset.py` reads base-detector outputs from `model_res_path` and
  `IncorrectIndices/train.json` for `FN` and `FP` segments.
- `agent/prompts/detection.py` contains combined false-negative and
  false-positive prompt templates.
- `agent/prompts/review.py` contains a combined-mode review prompt.
- `agent/review_agent.py` contains `combined_eval`,
  `combined_eval_all_in_one`, `combined_inference`, and
  `combined_inference_all_in_one`.
- `runtime/engine.py` routes combined modes to combined evaluation paths.

Safety conflicts with this project:

- ARGOS prompts request Python `inference` functions.
- ARGOS RepairAgent and ReviewAgent execute rule code with `exec`.
- ARGOS LLM client is coupled to OpenAI/Azure OpenAI environment variables.
- ARGOS paper reports Event-PA as the primary metric.
- ARGOS reproduction uses labeled train/validation/test data in ways that must
  stay isolated from the proposed multivariate extension policy.

## Paper-Code Alignment Matrix

| Paper element | Pinned-code evidence | Alignment status | Protocol action |
|---|---|---|---|
| Detection/Repair/Review agent loop | `runtime/engine.py`, `agent/detection_agent.py`, `agent/repair_agent.py`, `agent/review_agent.py` | present | Reproduce only in isolated ARGOS sandbox after approval. |
| Rule-only mode | README `train-LLM-only`; driver mode exists | present | Candidate first reproduction target, but real LLM is not approved in TASK-022. |
| Parallel top-k rule generation | README `train-LLM-only-parallel`; selector package exists | present | Audit-only for TASK-022; future run requires provider approval. |
| Evolutionary mode | README `train-evolution`; mutate agent exists | present but not central to paper Aggregator question | Keep out of initial paper-faithful reproduction unless explicitly selected. |
| Detector-plus-rule Aggregator | paper describes Aggregator; code has combined FN/FP paths | partially present, underdocumented | Requires DEC-027 before execution. |
| Base detector selection | paper selects the highest training score detector | not fully reproducible from pinned code alone | Requires baseline artifact protocol and EasyTSAD/model-output mapping. |
| Historical combined README/docs | current README omits combined examples | unresolved | Fetch full upstream history or request upstream release guidance before claiming exact reproduction. |
| LLM-generated Python execution | ARGOS executes generated Python | conflicts with project safety policy | Only allowed in a future isolated sandbox with explicit approval; never in production `paperworks` runtime. |
| Event-PA primary metric | paper uses Event-PA F1 | conflicts with extension default | Reproduction may report it as paper-faithful; extension keeps PA-free primary metrics. |

## Reproduction Protocol

### Stage A: Static Reproduction Audit

Status: completed by TASK-022.

Allowed actions:

- inspect paper text;
- inspect pinned ARGOS files;
- inspect local git metadata;
- record protocol, risks, and decisions.

Forbidden actions:

- real LLM calls;
- provider credential use;
- execution of LLM-generated Python;
- full ARGOS run;
- changes to the `paperworks` proposed-method pipeline.

### Stage B: Offline Harness Design

Future approval required.

Required before starting:

- resolve DEC-027;
- select exact ARGOS reproduction commit or historical commit;
- define whether initial reproduction targets rule-only or detector-plus-rule;
- define local-only synthetic or public non-restricted fixture;
- define how generated Python will be sandboxed or replaced by fixed stubs;
- define artifact locations ignored by Git for provider prompts/responses and
  generated code.

### Stage C: Paper-Faithful ARGOS Reproduction

Future approval required.

Required before starting:

- explicit permission for real provider calls, or a mock-only reproduction
  alternative;
- exact dataset edition and preprocessing route for KPI/Yahoo or other
  paper-matching public data;
- exact base-detector output schema for combined FN/FP paths;
- explicit policy for Event-PA as paper-faithful reproduction metric only;
- complete run manifest with commit, dependencies, config, provider metadata,
  seeds, prompt hashes, response hashes, and generated-rule hashes.

### Stage D: SWaT Univariate Transfer

Future approval required.

Required before starting:

- DEC-007 must remain respected for any final SWaT claim;
- use local/Kaggle staging only for debugging unless official iTrust data is
  approved;
- do not expose raw SWaT rows/windows to a provider;
- decide whether univariate ARGOS transfer uses safe JSON DSL or an isolated
  Python-rule sandbox.

### Stage E: Multivariate Extension

Future approval required.

Allowed only after reproduction lessons are documented. The extension must
remain project-owned and must preserve:

- JSON DSL rule artifacts;
- deterministic verification authority;
- runtime LLM-free execution;
- no execution of LLM-generated Python;
- PA-free primary evaluation policy.

## Required Future Decisions

Before any ARGOS reproduction run:

- Select the exact ARGOS source route:
  - current pinned commit `6b24161`, or
  - historical commit/release that better matches the paper.
- Select initial reproduction target:
  - rule-only first, or
  - detector-only plus combined rule-detector aggregation.
- Decide whether real LLM calls are allowed.
- Decide whether LLM-generated Python may be executed in an isolated sandbox.
- Decide whether Event-PA is allowed as paper-faithful reproduction metric.
- Define base-detector artifact schema and source for combined FN/FP modes.
- Define where generated rules, prompts, responses, and run logs may be stored.

## Gate A Conclusion

ARGOS_REPRODUCTION_GATE_A may be considered protocol-prepared, not
run-approved. The current pinned code contains the main agent loop and combined
mode code paths, but the paper-code alignment for the Aggregator workflow is
not resolved enough to run or claim faithful reproduction.
