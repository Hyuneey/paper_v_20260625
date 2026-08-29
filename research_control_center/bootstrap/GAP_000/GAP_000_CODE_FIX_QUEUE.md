# GAP-000 Code Fix Queue

## Must Fix

### GAP-001 — final authority contract
- Affected: task construction validity, canonical contracts, V4 descriptors/evaluator, runtime authorization.
- Intended behavior: one versioned scientific execution authority or a verified bridge with lossless/rebinding evidence.
- Tests: projection, conformance, stale authority, wrong relation/numeric/portfolio/hash rejection.
- Preserve: every PILOT V1 rule, descriptor, registry, prediction, trace hash, and metric.

### GAP-002 — D1 durable pre-label gate
- Affected: D1 INNER/future execution custody and prediction artifact state machine.
- Intended behavior: atomic persist, close, reopen/replay, authorize labels, post-metric byte equality.
- Tests: mutation, ordering, interrupted write, stale bytes, premature label access.
- Preserve: frozen D1 pilot and its qualification.

## Fix Before Specific Experiment

### GAP-006 before EXP-01
Correct or ablate diagonal/candidate masking before Top-K; test empty sets, self exclusion, mask order, and exported universe closure.

### GAP-005 before EXP-03
Separate construction failure taxonomy; test every transition and call-budget outcome.

### GAP-010 before EXP-05
Materialize the selected runtime trace and bind the renderer; test field and provenance fidelity.

## Optional Hardening

- GAP-012: enforce file/sampling contracts and source-bind the cross-arm aggregator.
- GAP-013: static entrypoint-to-split and authority conformance.
- GAP-011: fresh-machine capsule and rehearsal.

No experiment belongs in this queue, and no fix was implemented by GAP-000.
