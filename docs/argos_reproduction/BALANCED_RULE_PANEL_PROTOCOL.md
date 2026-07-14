# Balanced Rule Panel Protocol

TASK-035B first runs all 146 frozen executable cohort rules on the full inner-selection values of their own KPI. Containers receive values only. If any KPI retains fewer than ten contract-valid rules, processing stops before inner labels are loaded.

For each KPI, eligible rules are grouped by the five frozen anchors and sorted by rule SHA-256. Anchors are visited in their frozen rank order through repeated round-robin passes until exactly ten rules are selected. This API accepts no labels or metrics. The resulting 100-rule panel is hash-frozen before labels become available.

Panel membership is balanced by candidate count and broad anchor representation. It is not a performance-selected candidate pool.
