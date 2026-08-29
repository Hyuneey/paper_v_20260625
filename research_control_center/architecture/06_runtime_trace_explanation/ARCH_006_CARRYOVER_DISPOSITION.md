# Carryover disposition

| Source | Finding | Disposition | ARCH-006 evidence |
|---|---|---|---|
| ARCH-000 / ARCH-005 | frozen task trace versus canonical `RuntimeTraceV1` | PARTIALLY_RESOLVED | relationship is now classified `NON_EQUIVALENT`, with only terminal-outcome overlap; a versioned continuous-step trace bridge remains absent |
| ARCH-001 | D1 lacks durable prediction-file-before-label gate | REQUIRES_FUTURE_GOVERNANCE_FIX | process-local prediction is hash/factory validated before labels, but no durable pre-label bytes or state-machine gate exist |
| ARCH-003 | runtime values match construction values but authority identity is separate | RESOLVED_FOR_FROZEN_D1 | V4 evaluator consumes the rebound runtime authority; equality does not collapse identities |
| ARCH-005 | V4 authority plane versus canonical RuleV1 | RESOLVED | frozen runtime is explicitly mapped to the V4 bridge; canonical runtime is reference-only for this result |
| ARCH-005 | accepted versus runtime authorized | RESOLVED | D1 runs only after portfolio, evaluator, private registry, grant, bridge, frame, and census custody checks |
| ARCH-010 future | episode and metric semantics | DEFER_ARCH_010 | ARCH-006 proves only that episodes are downstream deduplicated metric constructs |

No frozen result requires replacement. The open items are future governance and interoperability work.
