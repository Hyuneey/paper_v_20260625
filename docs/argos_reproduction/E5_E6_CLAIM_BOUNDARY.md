# E5/E6 Claim Boundary

TASK-037C is a generic frozen-rule diagnostic complementarity experiment.

The max/min operators match the audited ARGOS fusion semantics, but the
TASK-035B rules were generated independently of detector false-negative and
false-positive subsets. TASK-037C therefore does not reproduce the paper's
error-conditioned rule training or complete Aggregator.

Allowed conclusions are limited to directional diagnostics: detector false
negatives recovered and false positives added by union, detector false
positives removed and true positives lost by intersection, disagreement
accounting, and sensitivity of these effects to the unresolved official LSTMAD
variant.

The task cannot establish fusion superiority, identify the true ARGOS detector
variant, select a final fusion arm, reproduce a benchmark, or report sealed-test
performance. Paper-faithful FN/FP rule generation and full Aggregator
evaluation remain future TASK-037D/E work.
