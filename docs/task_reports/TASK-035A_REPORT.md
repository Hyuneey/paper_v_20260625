# TASK-035A Report

## Status

`insufficient_rule_yield`

TASK-035A completed the pre-registered E2X-G generation, static-audit, and
container runtime-contract procedure. It did not satisfy the frozen adequacy
gate and does not authorize TASK-035B.

## Frozen cohort

- Selected KPI series: 10
- Generation anchors: 50
- Registered provider slots: 100
- Requests sent: 100
- Provider responses with non-empty text: 84
- Provider errors: 0
- Transport errors: 0
- Automatic or response-driven retries: 0
- RepairAgent or ReviewAgent calls: 0

The two requests for every anchor were byte-identical. All requests were built
before provider access. Test values and labels were not parsed; the separate
ground-truth package was not accessed.

## Rule yield

- Rules extracted: 61
- Static-valid rules: 61
- Distinct extracted rule hashes: 61
- Container-executable rules satisfying shape/domain checks: 55
- Runtime failures: 6
- Responses without an extractable rule: 39
- Terminal slot records: 100

Four KPI series had at least seven executable rules. Several series failed the
minimum of five executable rules or three distinct executable rule hashes, and
the total executable count was below the frozen minimum of 70. No threshold was
lowered and no replacement calls were made.

## Lineage note

Provider capture ran from clean Commit A `c3d3933`. The first container attempt
stopped before any generated rule executed because Windows newline conversion
changed quarantined-file byte hashes. Commit `7b03bfd` changed quarantine writes
to exact UTF-8 LF bytes, after which the same captured responses were re-audited
without provider calls and the 61 static-valid rules were executed once. The
aggregate reports contain module, config, approval, image, and artifact hashes.

## Claim boundary

This result is a generation-cohort and runtime-plumbing diagnostic only. It
does not measure KPI anomaly-detection performance, rule accuracy, explanation
quality, detector comparison, fusion performance, or sealed-test behavior. It
is not a benchmark or thesis-performance result.
