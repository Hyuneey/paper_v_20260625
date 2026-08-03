# Continuous-Step Rule V2 Migration Plan

This is a plan, not Rule v2. A future additive canonical version must live
beside Rule v1 with an independent schema and parser. Continuous rules must
never pass through the Rule v1 parser or broaden Rule v1 fields in place.

The planned trigger binds `sustained_continuous_step`, one variable, explicit
step direction, and references for threshold, pre/post windows, stability, and
refractory period. The effect binds `delayed_change`, one target, explicit
direction, and references for response threshold, lag, and response window.

One source, one target, missing expected response, anomaly/abstain,
normal-reference/evidence/edge bindings, complexity, history, verifier
authority, and LLM-free runtime remain mandatory. All TASK-032 hashes must be
preserved.
