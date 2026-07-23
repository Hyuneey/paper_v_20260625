# TASK-037E Inner Selection Report

FN and FP rules were selected independently on the frozen inner partition.
Every detector/KPI/direction unit included a no-op candidate.

- FN rule selected: 19
- FN no-op selected: 1
- FP rule selected: 2
- FP no-op selected: 18
- Joint FN/FP pair search: not performed
- Outer metrics seen during selection: false
- Sealed-test access: false

The TASK-037E outer partition is a previously exposed follow-up validation partition. Rule generation used only the generation partition and rule selection used only the inner partition, but the broader experiment design followed prior inspection of outer results. Therefore TASK-037E does not support an untouched confirmatory superiority claim.
