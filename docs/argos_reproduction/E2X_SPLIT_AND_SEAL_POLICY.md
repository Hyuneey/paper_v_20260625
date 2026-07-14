# E2X Split and Seal Policy

E2X uses chronological, exhaustive, half-open ranges with no shuffle, purge,
or artificial gap:

1. generation: `[0, generation_end)`
2. inner selection: `[generation_end, outer_train_end)`
3. outer validation: `[outer_train_end, train_pool_end)`
4. sealed test: `[train_pool_end, N)`

TASK-035A parses generation, inner, and outer value/label prefixes only. Inner
and outer labels are counted solely for pre-registered cohort eligibility.
They are not used for rule selection or performance. Test values and labels are
never parsed.

E2X-S and E2X-V remain deferred. E2X-T and E3 remain sealed and unauthorized.
No later task may alter these boundaries based on TASK-035A rule outputs.
