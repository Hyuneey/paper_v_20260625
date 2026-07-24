# Four-Branch Selection Protocol

TASK-038D applies one frozen selection procedure to `A0`, `A1`, `A2`, and
`A3`. The immutable executable-output counts are 83, 96, 82, and 96,
respectively. These 357 logical records are not deduplicated across branches.

Each branch, detector variant, KPI, and FN/FP direction defines one selection
unit. All matching executable outputs and one explicit no-op enter the unit.
FN and FP are selected independently, with at most one non-no-op per unit.
The direct PA-free TASK-037E ranking and exact no-op tie rule are reused.

Candidate predictions and detector lineage are hash-verified and frozen before
inner labels are loaded. A0 must reproduce all forty TASK-037E selections
before A1-A3 results are accepted. No provider, agent, outer partition, or
sealed-test access is permitted.
