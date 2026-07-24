# Review Branch Effect Boundary

TASK-038C is a four-branch component-wise ablation with structural
non-applicability, not a balanced causal factorial experiment.

For the 83 initially executable slots, `A2` and `A3` share the same parent
condition but receive independent Review generations. Differences between
those branches measure Review-generation variability and are not a
RepairAgent interaction.

For the 13 initially failed slots, `A2` is non-applicable. `A3` compares one
shared TASK-038B repaired parent with its independently reviewed output. This
subgroup estimates the incremental inner-only effect of Review after Repair,
not a full factorial interaction.

Attempted-call endpoints retain invalid and non-executable revisions in their
denominators. Numeric performance deltas among executable revisions are
separately labelled conditional descriptive results. A harmful or invalid
Review output cannot be silently reverted.
