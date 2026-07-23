# Error-Conditioned Rule Inner Selection Protocol

TASK-037E registers all 83 TASK-037D executable rules before inner execution.
Each rule remains bound to one detector variant, KPI, and FN/FP direction.

Every rule executes twice in a fresh rootless Podman container on its complete
inner value array. The container receives no labels, detector prediction,
outer artifact, test artifact, or credential. Rule hash, input hash, output
shape/domain, prediction hash, and positive count must match exactly.

All terminal statuses and valid prediction hashes are frozen before inner
labels are loaded. FN and FP selection then occurs independently for each of
the twenty detector/KPI units. Every unit includes an explicit no-op candidate,
and at most one rule may be selected per direction. Exact complete ties with
no-op resolve to no-op.

Selection uses direct PA-free point/event metrics and the frozen DEC-069
rankings. It performs no joint FN/FP pair search, rule ensemble construction,
point adjustment, threshold search, detector selection, or outer inspection.

The TASK-037E outer partition is a previously exposed follow-up validation
partition. Rule generation used only the generation partition and rule
selection used only the inner partition, but the broader experiment design
followed prior inspection of outer results. Therefore TASK-037E does not
support an untouched confirmatory superiority claim.
