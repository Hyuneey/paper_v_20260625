# Diagnostic Versus Paper-Faithful Fusion

## Track D: diagnostic composition

Track D reuses the frozen TASK-035B `Best-1`, `Top-3 OR`, `Coverage-3 OR`, and
`All-10 OR` rule arms.

- FN diagnostic: `max(detector, frozen_rule_arm)`
- FP diagnostic: `min(detector, frozen_rule_arm)`

This tests whether the existing generic rule pool is complementary to a
detector. It is not paper-faithful ARGOS because those rules were not generated
from detector FN and FP subsets.

## Track P: paper-faithful error conditioning

Track P requires new, separately approved FN rules from detector FN segments
contrasted with normal/TN evidence, and FP rules from detector FP segments
contrasted with anomaly/TP evidence. The full Aggregator begins from the
detector label, lets FN rules correct only zeros, and lets FP rules correct only
ones.

Later reports must separately quantify recovered FN versus added FP, and
removed FP versus removed TP. TASK-037A executes neither track and makes no
fusion-superiority claim.

Frozen FN diagnostics are detector FN count, recovered FN count/rate, added FP
count, and net recall, point-F1, and event-recall changes. Frozen FP diagnostics
are detector FP count, removed FP count/rate, removed TP count, and net
precision, point-F1, and event-recall changes.
