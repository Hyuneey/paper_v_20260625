# Parameter v1 Model and Phase 1 Adapter

`CalibrationParameterV1` and its nested frozen records cover the canonical
parameter-registry document. TASK-032C supports only delayed-response roles:

- `lag_minimum`, `lag_maximum`, and `response_delay` under `PARAM-LAG-*`;
- `tolerance` under `PARAM-TOL-*`;
- `persistence_duration` under `PARAM-DURATION-*`;
- `minimum_support` under `PARAM-SUPPORT-*`.

Registry-first parsing verifies the self-hash, one-source/one-target scope,
confidence ordering, support counts, stability/status coherence, and approved
record attribution. These are document-integrity checks, not proof that the
calibration method or value is scientifically correct.

The Phase 1 adapter requires an explicit mapping of legacy parameter name and
method to target ID, role, calibration method, provenance, support, stability,
confidence, and uncertainty. It preserves the numeric value and unit exactly.
It never infers a mapping from a free-form name alone.

Adapter-created status is limited to `proposed`, `calibrated`, `unstable`, or
`rejected`; approver fields are always null. `approved` output is prohibited.
Synthetic-smoke records cannot be promoted beyond `proposed`.
