# ARCH-006 mismatches

| ID | Documented or tempting wording | Actual implementation | Type | Scientific impact | Severity | Recommended future action |
|---|---|---|---|---|---|---|
| A006-M01 | frozen D1 runs canonical RuleV1/RuntimeV1 | frozen D1 runs the task-specific V4 real bridge | RUNTIME_AUTHORITY | wrong authority attribution | HIGH | keep V4 terminology; design an explicit bridge before claiming canonical runtime |
| A006-M02 | frozen D1 trace is `RuntimeTraceV1` | only a task-specific terminal trace hash and compact record are persisted | TRACE_SCHEMA | canonical satisfaction-step claims are unsupported | HIGH | version and materialize a continuous-step trace schema |
| A006-M03 | frozen D1 explanations are trace-grounded | canonical renderer is not wired to the V4 trace | TRACE_EXPLANATION | frozen-result explanation claims are unsupported | HIGH | add an authority-bound V4 trace/renderer bridge before EXP-05 |
| A006-M04 | D1 was durably persisted before labels | prediction was validated in memory and written publicly only after metrics | LABEL_BOUNDARY | governance strength can be overstated | HIGH | durable atomic write/replay/state gate in future validation |
| A006-M05 | frozen prediction is immutable | top-level dataclass and tuple are frozen but nested record dictionaries are mutable | FREEZE | concurrent mutation is not structurally impossible | MEDIUM | deep-immutable records plus byte gate |
| A006-M06 | 788 point alarms | 788 anomalous rule records occupy 630 unique decision seconds | STATUS_SEMANTIC | overcounts physical alarm points | MEDIUM | say rule-record alarms; report unique points separately when authorized |
| A006-M07 | all ten numeric values are dynamically read by the evaluator | three are dereferenced; seven are validated references compiled into frozen constants/policies | NUMERIC_RUNTIME | obscures implementation semantics | MEDIUM | distinguish dynamic calibration roles from frozen protocol constants |
| A006-M08 | a separate persistence threshold is evaluated | source stability and a three-row target median are used; no independent target-persistence predicate exists | RUNTIME_SEMANTIC | overstates rule complexity | MEDIUM | use exact source-stability/response-window wording |
| A006-M09 | source did not trigger means PASS or ABSTAIN | non-trigger rows generate no opportunity and no outcome | OUTCOME_SEMANTIC | misstates denominator and trace scope | MEDIUM | describe opportunity-based evaluation |
| A006-M10 | ABSTAIN is normal | ABSTAIN means insufficient boundary context for a formed opportunity | OUTCOME_SEMANTIC | changes operational interpretation | MEDIUM | preserve three-way outcome taxonomy |
| A006-M11 | alarm episodes are runtime outputs | episodes are formed downstream for metrics after point-index deduplication | RUNTIME_METRIC | conflates detection and scoring | LOW | defer metric details to ARCH-010 |
| A006-M12 | frozen R0 proves all runtime modes are LLM-free | only frozen fixed-rule R0/D1 has zero LLM/provider dependency | FUTURE_R1 | blocks correct future comparison framing | LOW | scope the wording and preregister R1 inputs |
| A006-M13 | deterministic explanations establish human usefulness | only canonical structural/template fidelity is tested | CLAIM_BOUNDARY | human-usefulness claim unsupported | LOW | retain UNVALIDATED until human evaluation |

Counts: 13 total; 0 critical; 4 high; 6 medium; 3 low.
