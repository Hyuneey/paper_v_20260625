# ARCH-008 Attack-event Evaluation

The frozen label evaluator defines an attack event as a maximal contiguous file-local run of exact binary label `1`. The frozen test1 evidence contains 14 operationally defined event units; statistical independence is not established.

An event is detected when at least one D1 alarm episode has half-open interval overlap with it. Multiple alarm seconds or episodes inside the same event still contribute one detected event. No tolerance, pre-event extension, or post-event extension is applied by the audited overlap predicate.

| Quantity | Frozen value |
|---|---:|
| Total attack events | 14 |
| D1-detected events | 13 |
| D1-missed events | 1 |
| Attack-event Recall | 13/14 = 0.9285714285714286 |

This is event-level overlap recall. It is neither precision nor attack-point recall. Event coordinates and the identity of the single missed event remain private; no existing sanitized artifact classifies that miss, so its mechanism is **UNKNOWN**.
