# ARCH-006 Independent QA Report

## Verdict

`PASS`

All 18 required QA questions are satisfactory. The reviewer made no file edits.

## Required questions

| # | Question | Result |
|---:|---|---|
| 1 | Is the actual V4 frozen runtime mapped? | PASS |
| 2 | Is trigger semantics source-supported? | PASS |
| 3 | Is target-response semantics source-supported? | PASS |
| 4 | Are tolerance and persistence accurate? | PASS |
| 5 | Are PASS, FAIL, and ABSTAIN accurately defined? | PASS |
| 6 | Is D1 aggregation accurately mapped? | PASS |
| 7 | Is runtime prediction separated from metric episodes? | PASS |
| 8 | Is the task-specific trace mapped? | PASS |
| 9 | Is RuntimeTraceV1 comparison conservative? | PASS — NON_EQUIVALENT with partial terminal overlap |
| 10 | Is prediction-before-label ordering supported? | PASS — in-memory authority only |
| 11 | Is the durable-freeze limitation explicit? | PASS |
| 12 | Is determinism accurately classified? | PASS — fixed bytes and runtime semantics qualification retained |
| 13 | Are frozen R0 LLM calls confirmed zero? | PASS |
| 14 | Is the explanation renderer accurately mapped? | PASS |
| 15 | Is structural fidelity separated from human usefulness? | PASS |
| 16 | Are causal and root-cause claims excluded? | PASS |
| 17 | Is the future R1 outcome-leakage boundary explicit? | PASS |
| 18 | Did the audit execute zero scientific runtime? | PASS |

## Precision correction

The first review requested one wording correction: the 10-second same-source policy must state
that adjacent candidates form a single-link cluster, the largest absolute step amplitude is
retained, and an exact tie keeps the earliest index before inclusive ±2-second cross-source
isolation. The coordinator applied this to the state, state machine, Korean report, dashboard
source, and generated user summary. The reviewer confirmed the correction.

## Counts and validation

- Mismatches: 13 total — 0 critical, 4 high, 6 medium, 3 low
- Registry validator: PASS
- Full RCC tests: 76/76 PASS
- Focused ARCH-006 tests: 5/5 PASS
- Privacy exposures: 0
- Scientific/runtime executions, LLM calls, label accesses, and test2 accesses: 0

Required corrections remaining: none.
