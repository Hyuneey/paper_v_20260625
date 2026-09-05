# DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access

Status: `USER_DECISION_REQUIRED`

No attack/test payload, label value, scenario interval, scenario target, or real eligibility was accessed while preparing this gate.

## Scope

One conditional approval covers exactly HAI23 test2 (38 nominal scenarios), HAI22 (58), and HAI21 (50). Phase A permits positive-allowlist feature projection and all frozen-method predictions in the fixed HAI23 → HAI22 → HAI21 operational order. Phase B is technically gated and becomes usable only after the exact global cell census and `GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED` receipt validate.

## Frozen authorities

- method bundle: `dab320da47489e5093862b7c4675523c3e6b710faceb753e7f39c8e56f002fe2`
- metric authority: `de9b083879ecfc31feb3c300dda28d0b94bb7d544498511f7e030ebf86567e4d`
- P1 custodian: `3b86c98dbd8f5e4fa71eed3963ec639e2e08a4a4e0af056387f33f98de628794`
- global custody: `dee24b1ad99f75ddc0d0113eed4fa2a5dc0dc07787c4b4b6efc5817b58598499`
- preregistration: `f337a58178a2aca0c4333a69700cafd8d17bf22ec8bc5af78a3acd68e1055950`
- Fusion: `587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc`
- HAI23 detector replay: `1234517f244f45ed5a9b6e7b555138773f67891e28c27dd28404b1d71c959e2d`
- HAI23 detector private hash binding: `abe9b3abfdf792b247492d7cc9e195c7f54ece57fd7b9337d38e04efd7241780`
- HAI23 PCA fit/threshold: `f1f29e8a51f2c3fd81654b2b11ab86c3208446db8effdb9e86902bb9fc2ca530` / `58d38959d47b3dced9a450bfd8bde9af1dcb8fab0a013e4145c4a657ff4d284b`
- HAI23 IF fit/threshold: `425533c995a71b6c8dd7bd20ada3c4c060a3c6e2d5859268271bcfd6f3f44780` / `4f143fed3914593b31db7ba8d93ad08ec241307b2d091675e0d0f757603daa5d`
- HAI22 detector: `3abe6aeb898e8ea0bbca9eb41bab968d6a53232aee3c70a3fc5885008ffe67c4`
- HAI21 detector: `0eb58f17096d5ca0d5bbbc4c9d51a7220dc45d19830e00671a0fbfaee78315d6`

## Non-negotiable execution

All primary and secondary prediction cells must terminate as `SUCCESS` or explicit `METHOD_FAILURE`; failure is never coerced to no alarm, no rule, or miss. No label/scenario value may be read between panels. After lease opening, predictions, models, portfolios, thresholds, Fusion, and eligibility logic are immutable. Independent QA recomputes denominators, hits/misses, Wilson intervals, delays, false burden, eTaPR, paired tables, overlap, and incremental metrics from frozen authorities only.

No provider call, GDN training, method redesign, point adjustment, cross-version IID pooling, or professor submission is authorized.
