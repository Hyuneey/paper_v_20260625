# Error-Conditioned Rule Protocol

TASK-037D constructs `paper_aligned_error_conditioned_one_shot_rules` from
frozen TASK-037B generation errors. It retains both unresolved LSTMAD variants,
all ten KPI series and both FN and FP directions.

Each potential cell is one detector variant, KPI and direction. FN targets
intersect detector FN segments and are contrasted with pure TN chunks. FP
targets intersect detector FP segments, contain no anomaly labels, and are
contrasted with TP-supported abnormal chunks. All data are confined to the
frozen generation partition.

Up to three distinct 1,000-point target chunks are selected chronologically by
the predeclared evenly distributed rank policy. Each target receives exactly
one provider request. No retry, replacement, prior rule, repair, review,
selection, performance evaluation or fusion occurs.

Static-valid rules are run separately on target and contrast values in the
frozen rootless Podman runtime. Labels and detector predictions are never
mounted. Passing this gate establishes only syntax, safety and input/output
runtime compatibility.

## Frozen support outcome

- Potential cells: 40
- Eligible FN cells: 20
- Eligible FP cells: 14
- Zero-error FP cells: 2
- FP cells without a distinct valid 1,000-point target: 4
- Frozen requests: 96

Unsupported and zero-error cells receive no request and remain explicitly
reported.
