# TASK-022 Completion Report

TASK-022 is an audit/protocol task only. It does not approve real LLM calls, execution of LLM-generated Python, full ARGOS experiments, or changes to the paperworks proposed-method pipeline.

## Summary

TASK-022 prepared the ARGOS reproduction audit and paper-code alignment
protocol. It treats TASK-000 through TASK-021 as multivariate-extension
feasibility infrastructure, not as an ARGOS reproduction.

## Outputs

- `docs/ARGOS_REPRODUCTION_PROTOCOL.md`
- `docs/phase_gates/ARGOS_REPRODUCTION_GATE_A.md`
- `docs/task_reports/TASK-022_ARGOS_REPRODUCTION_AUDIT.json`
- `docs/task_reports/TASK-022_REPORT.md`
- `TASKS/TASK-022_ARGOS_REPRODUCTION_AUDIT.md`

## Audit Findings

- ARGOS local reference is pinned at
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- ARGOS repository license is MIT.
- Current ARGOS README documents `train-LLM-only`,
  `train-LLM-only-parallel`, and `train-evolution`.
- Current ARGOS code still exposes `train-combined-fn`,
  `train-combined-fp`, and `eval-combined`.
- Current ARGOS code contains combined false-negative/false-positive prompts,
  combined review prompts, `combine_labels`, combined evaluation, and combined
  inference code paths.
- The paper's detector-plus-rule Aggregator workflow is therefore partially
  present in code but underdocumented in the pinned README.
- Historical README inspection is unresolved because the local ARGOS reference
  is a partial clone and older README blobs require remote fetch.

## Claim Boundary

Allowed TASK-022 claims:

- A paper-code alignment protocol now exists.
- The pinned ARGOS code contains both documented rule-only modes and
  underdocumented combined-mode code paths.
- A future reproduction run needs a decision on current pinned commit versus a
  historical paper-matching commit.

Prohibited TASK-022 claims:

- ARGOS has been reproduced.
- The paper's Aggregator implementation is fully runnable as-is.
- A real LLM provider has been validated.
- LLM-generated Python execution is approved.
- The multivariate `paperworks` method has inherited ARGOS evaluation policy.
- Any benchmark or thesis performance claim.

## Required Future Decisions

- Resolve DEC-027 before any real ARGOS reproduction run.
- Decide whether to start with rule-only reproduction or detector-plus-rule
  reproduction.
- Decide whether to approve real LLM calls.
- Decide whether generated Python may be executed in an isolated sandbox.
- Decide whether Event-PA is allowed only as paper-faithful reproduction metric.
- Define the base-detector output schema required by `train-combined-fn/fp`.

## Commands Run

```powershell
git status --short
git log -1 --oneline --decorate
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos rev-parse HEAD
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos log -1 --oneline --decorate
Get-Content -LiteralPath external\argos\LICENSE -TotalCount 40
Get-Content -LiteralPath external\argos\README.md -TotalCount 220
rg -n "train-LLM-only|train-LLM-only-parallel|train-evolution|train-combined|combined|Aggregator|aggregation|false positive|false negative|FN|FP" external\argos
Select-String -LiteralPath external\argos\driver.py -Pattern "train-combined|eval-combined|train-LLM-only|train-evolution|choices|mode" -Context 2,4
Select-String -LiteralPath external\argos\common\common.py -Pattern "def combine_labels|train-combined-fn|train-combined-fp|false positive|false negative" -Context 2,12
Select-String -LiteralPath external\argos\agent\review_agent.py -Pattern "def combined_eval|def combined_inference|combine_labels|baseline|model_labels|rule_labels" -Context 2,8
Select-String -LiteralPath external\argos\datasets\dataset.py -Pattern "train-combined-fn|train-combined-fp|model_result_path|incorrect_segments|FN|FP" -Context 2,8
Select-String -LiteralPath external\argos\agent\prompts\detection.py -Pattern "DETECTION_AGENT_V3_COMBINED_FN_PROMPT_TEMPLATE|DETECTION_AGENT_V3_COMBINED_FP_PROMPT_TEMPLATE|build_detection_agent_prompt|train-combined" -Context 0,4
Select-String -LiteralPath external\argos\agent\prompts\review.py -Pattern "REVIEW_AGENT_COMBINED_PROMPT|train-combined|build_review_agent_prompt" -Context 0,8
Select-String -LiteralPath external\argos\agent\agent.py,external\argos\agent\repair_agent.py,external\argos\agent\review_agent.py -Pattern "exec\(|eval\(|run_with_timeout|OPENAI_AZURE|llm|Azure|client" -Context 1,4
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool docs\task_reports\TASK-022_ARGOS_REPRODUCTION_AUDIT.json
git diff --check
git ls-files dataset external
```

## Check Results

- ARGOS commit verification: passed.
- ARGOS license verification: passed.
- ARGOS read-only access policy: respected.
- Real LLM calls: not run.
- LLM-generated Python execution: not run.
- Full ARGOS experiment: not run.
- `paperworks` proposed-method pipeline changes: none.
- Raw SWaT row access: none.
- TASK-022 JSON validation: passed.
- `git diff --check`: passed.
- `git ls-files dataset external`: no tracked raw dataset or upstream reference
  files.

## Interpretation

The current pinned ARGOS snapshot is sufficient for a static reproduction audit
and for planning a future reproduction, but not sufficient to claim a faithful
paper reproduction. The paper's Aggregator path should be treated as an open
alignment issue until DEC-027 is resolved.
