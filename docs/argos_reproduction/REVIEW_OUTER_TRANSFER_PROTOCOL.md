# Review Outer Transfer Protocol

TASK-038E evaluates all 76 TASK-038C `reviewed_executable` outputs, including
selected and non-selected revisions. Each reviewed rule is compared with its
exact pre-review parent under the matching detector, KPI, direction, and
binary composition:

- FN: `max(detector, rule)`
- FP: `min(detector, rule)`

Parent and reviewed predictions are frozen before labels are loaded. The
paired report preserves inner and outer precision, recall, point-F1, and
FP/10k deltas and classifies transfer as positive, zero, negative, recovered
from an inner regression, identical, or another mixed pattern.

The A2 and A3 calls from identical initially executable parents were
independent stochastic revisions. Their differences are Review-generation
variability, not a Repair interaction. Outer transfer is descriptive because
the outer partition was previously exposed to the broader research program.
