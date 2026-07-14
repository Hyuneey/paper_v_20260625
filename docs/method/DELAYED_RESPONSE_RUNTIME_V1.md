# Delayed-Response Runtime v1

## Scope

TASK-032E executes one accepted delayed-response rule on immutable synthetic
windows. Inputs use one uniformly sampled binary source and one finite numeric
target; null target values are explicit missing inputs. No interpolation,
resampling, provider, LLM, generated Python, detector, or dataset reader is
used.

## Operational Semantics

A trigger is a transition into the configured source state. No trigger is an
evaluated nonviolation; one trigger is evaluated; multiple triggers abstain.
Starting in the trigger state abstains because no pre-trigger baseline exists.

The baseline is the target value immediately before the trigger. The runtime
searches the inclusive approved lag interval and accepts the first observation
whose target increase reaches the approved tolerance. Failure to find one is a
`missing_expected_response` violation.

The window must cover maximum lag, event-relative duration, and persistence
duration. Persistence is coverage-only in this MVP. Violations score `1.0` and
all other results score `0.0`; this is a binary plumbing score, not calibrated
anomaly severity. Severity and support records remain hash-bound and visible in
the trace but do not change the result.

## Abstention

Registered reasons are regime mismatch, missing input, multiple triggers,
missing pre-trigger baseline, insufficient coverage, parameter uncertainty,
and input-variable mismatch. Abstention is never an anomaly and carries no
binary rule label in the explanation.
