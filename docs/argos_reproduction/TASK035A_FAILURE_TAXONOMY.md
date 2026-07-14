# TASK-035A Failure Taxonomy

TASK-035A remains an immutable `insufficient_rule_yield` cohort. Before any
TASK-035AR request, its 45 non-executable slots are classified from retained
private metadata into aggregate-only categories. Tracked output contains only
counts by category and KPI plus output/reasoning-token summaries.

The diagnosis is generation-operability only. It does not inspect KPI
validation, outer validation, test values, test labels, or performance.
Response text, rule source, exception text, private paths, and KPI values are
never copied into the tracked taxonomy report. Ambiguous failures use
`unknown_sanitized`.

The frozen primary diagnosis is that sixteen responses exhausted the original
2,000-token output budget with 2,000 reasoning tokens and no visible response.
Secondary failures contain visible responses without one extractable Python
rule; tertiary failures pass static checks but fail isolated execution.
