# Continuous-Step Runtime Trace Plan

The future runtime is deterministic and LLM-free. Its trace must bind source,
step direction, pre/post aggregates, observed amplitude, threshold reference
and value, stability, event time, target, expected direction, lag, observed
response, response-threshold reference and value, violation, and abstention.

Incomplete windows, nonfinite inputs, an unauthorized operating regime, or a
file/split boundary may abstain. Invalid rules and parameter-binding failures
are authorization failures, not abstentions. Explanations may verbalize trace
facts but cannot invent causes, attack identities, hidden mechanisms,
variables, or numeric observations.

Runtime v1 is unchanged. TASK-039BR1 implements no runtime or rule execution.
