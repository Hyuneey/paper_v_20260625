# Balanced Rule Cohort Gate

The combined cohort contains all executable rules from the immutable 100-slot
TASK-035A cohort and the independent 100-slot TASK-035AR cohort. Duplicate
responses and rules are retained as reproducibility evidence. No performance-
based filtering is allowed.

TASK-035B is authorized only if all frozen TASK-035AR thresholds pass:

- at least 90 remediation non-empty responses;
- at least 75 remediation executable rules;
- at least 120 cumulative executable rules;
- at least 8 cumulative executable and 6 distinct rules for every KPI;
- at least 8 KPIs with 10 executable rules;
- at least 35 anchors with 2 executable rules;
- all 200 registered slots are terminal and all 100 remediation requests are
  consumed without retry.

The gate reports generation-operability and cohort balance only. It does not
measure rule accuracy, selection quality, validation performance, test
performance, detector behavior, or fusion behavior.
