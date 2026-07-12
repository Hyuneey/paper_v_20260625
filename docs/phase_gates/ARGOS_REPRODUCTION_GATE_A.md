# ARGOS_REPRODUCTION_GATE_A

TASK-022 is an audit/protocol task only. It does not approve real LLM calls, execution of LLM-generated Python, full ARGOS experiments, or changes to the paperworks proposed-method pipeline.

## Gate Status

- Status: protocol prepared
- Run approval: not granted
- Starting repository commit: `5ce6647`
- ARGOS reference commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- ARGOS license: MIT

## Gate Findings

- The pinned ARGOS README documents `train-LLM-only`,
  `train-LLM-only-parallel`, and `train-evolution`.
- The pinned ARGOS code still exposes `train-combined-fn`,
  `train-combined-fp`, and `eval-combined`.
- The ARGOS paper describes detector-plus-rule aggregation as a central
  accuracy-guarantee mechanism.
- Current code contains combined-mode code paths, but the runnable,
  paper-faithful Aggregator protocol is underdocumented at the pinned README.
- Historical README blobs were not inspected because the local ARGOS clone is
  partial and older blobs require remote fetch.

## Pass Criteria Met

- ARGOS commit and license were verified locally.
- Paper-code alignment risks were documented.
- A safety-controlled reproduction protocol was defined.
- Required future decisions were recorded.
- No real LLM provider was called.
- No generated Python was executed.
- No full ARGOS experiment was run.
- No proposed-method pipeline code was modified.

## Not Approved

- real provider calls,
- API key use,
- execution of LLM-generated Python,
- full ARGOS reproduction runs,
- Event-PA adoption for the multivariate extension,
- changes to `src/paperworks` runtime or planning behavior,
- any benchmark or thesis performance claim.

## Required Before Gate B

- Resolve DEC-027.
- Decide current pinned commit versus historical paper-matching commit.
- Decide rule-only-first versus detector-plus-rule-first reproduction.
- Define base-detector artifact format for `train-combined-fn/fp`.
- Define isolated sandbox policy for any generated Python execution.
- Define provider, prompt, response, and generated-rule retention policy.
