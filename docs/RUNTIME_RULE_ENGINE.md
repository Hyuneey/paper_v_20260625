# Runtime Rule Engine

TASK-010 implements an LLM-free deterministic runtime rule engine.

The public interface is:

```python
engine = RuntimeRuleEngine(registry=registry)
engine.load_library(verified_rule_library)
evaluation = engine.evaluate(time_series_batch)
```

The runtime imports no planning or LLM provider modules. It accepts only verified
DSL rules and canonical rule-view batches.

## Synthetic Smoke Policy

The tracked config is:

- `configs/runtime/task010_synthetic_smoke.json`

Synthetic smoke runtime semantics:

- source view: `canonical_rule_view`
- severity mode: binary
- binary severity: `1.0`
- aggregate score: max fired-rule severity
- alarm merge: overlapping or adjacent intervals within one sampling period

This policy is an implementation smoke contract only. It is not a final SWaT
severity, scoring, or alarm-merge policy.

## Runtime Artifacts

`RuntimeEvaluation` stores aggregate runtime output:

- firing records,
- alarm intervals,
- deterministic explanations,
- aggregate rule score,
- runtime statistics,
- config hash,
- library ID and batch ID.

`RuntimeExplanation` fields are derived from rule AST and observed violation
values:

- `alarm_start`
- `alarm_end`
- `rule_id`
- `variables`
- `expected_relation`
- `observed_violation`
- `calibration_basis`
- `candidate_provenance`
- `source_view`
- `sampling_period_seconds`

Tracked reports must not include reconstructive raw SWaT sequences.
