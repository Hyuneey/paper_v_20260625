# DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access

Status: `USER_DECISION_REQUIRED`

No attack/test payload, label value, scenario interval, scenario target, or real eligibility was accessed while preparing this gate.

## Scope

One conditional approval covers exactly HAI23 test2 (38 nominal scenarios), HAI22 (58), and HAI21 (50). Phase A permits positive-allowlist feature projection and all frozen-method predictions in the fixed HAI23 → HAI22 → HAI21 operational order. Phase B is technically gated and becomes usable only after the exact global cell census and `GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED` receipt validate.

## Frozen authorities

- method bundle: `20cdffa228b6cc920e3ba665651cf2c8b799f4560886ef4b5a3449e3d1e857ed`
- metric authority: `de9b083879ecfc31feb3c300dda28d0b94bb7d544498511f7e030ebf86567e4d`
- P1 custodian: `3b86c98dbd8f5e4fa71eed3963ec639e2e08a4a4e0af056387f33f98de628794`
- global custody: `dee24b1ad99f75ddc0d0113eed4fa2a5dc0dc07787c4b4b6efc5817b58598499`
- preregistration: `b5596bb09a26e3e5e6966f2940fe3cde74b659e1439accd6d3debbec31c1b1c9`
- Fusion: `587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc`
- HAI23 detector replay: `7de9423b7016bc8ff8e40df598f2be8c258acceafffcb237ee710e7b68dd0620`
- HAI22 detector: `3abe6aeb898e8ea0bbca9eb41bab968d6a53232aee3c70a3fc5885008ffe67c4`
- HAI21 detector: `0eb58f17096d5ca0d5bbbc4c9d51a7220dc45d19830e00671a0fbfaee78315d6`

## Non-negotiable execution

All primary and secondary prediction cells must terminate as `SUCCESS` or explicit `METHOD_FAILURE`; failure is never coerced to no alarm, no rule, or miss. No label/scenario value may be read between panels. After lease opening, predictions, models, portfolios, thresholds, Fusion, and eligibility logic are immutable. Independent QA recomputes denominators, hits/misses, Wilson intervals, delays, false burden, eTaPR, paired tables, overlap, and incremental metrics from frozen authorities only.

No provider call, GDN training, method redesign, point adjustment, cross-version IID pooling, or professor submission is authorized.
