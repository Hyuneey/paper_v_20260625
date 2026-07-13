# Captured Rule Container Boundary

This directory specifies a future container-only boundary for the fixed
TASK-026Q rule hash. TASK-027 does not build the image or execute the rule.

Execution remains blocked until a separate approval names the immutable image
digest, approves one synthetic non-KPI input, and keeps every control in
`configs/argos_reproduction/task027_semantic_audit.json` enabled. There is no
local subprocess fallback for captured rules.
