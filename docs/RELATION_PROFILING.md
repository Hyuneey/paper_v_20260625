# Relation Profiling and Calibration

TASK-006 implements the first supported relation profile:

```text
binary actuator changed_to 1.0 -> continuous sensor increase_within Delta t
```

The implementation is intentionally narrow. It accepts only `calibration_normal`
splits and `canonical_rule_view` data. GDN-view or test-split inputs are rejected
before any profile or calibration record can be produced.

## Synthetic smoke policy

The tracked config is:

- `configs/profiling/task006_synthetic_smoke.json`
- trigger: `changed_to` from `0.0` to `1.0`
- response: first positive target increase within `max_response_delay_samples`
- support gate: at least 2 matched normal responses
- delay calibration: empirical quantile `1.0`
- magnitude calibration: empirical quantile `0.0`
- irregular sampling policy: reject

This policy is an implementation smoke contract only. It is not a final SWaT
calibration policy and does not support performance claims.

## Artifacts

`RelationProfile` stores:

- trigger-event records,
- response-event records,
- delay and magnitude summaries,
- missing and right-censored counts,
- overlap counts for repeated trigger windows,
- source view, sampling period, config hash, split name, and upstream artifact IDs.

`CalibrationRecord` stores one numeric rule parameter and references the exact
relation profile and calibration split that produced it.

`RelationEvidencePack` stores aggregate planner input only:

- candidate pair,
- support counts,
- calibrated parameter values,
- calibration record IDs,
- recommended minimal rule family.

Evidence packs must not include raw SWaT rows or long raw sequences.
