# D1 prediction freeze and label boundary

## Proven order

```text
test1 features
→ complete V4 census and rule evaluation
→ build ScientificRulePredictionArtifactV1
→ compute artifact hash
→ register factory/weak-reference custody
→ replay-validate prediction
→ label loader revalidates token and prediction
→ label file hash/open/parse
→ metrics
→ public prediction JSON write
```

Supported wording:

> D1 prediction authority was label-blind and validated in memory before label-test1 access.

Unsupported wording:

> D1 prediction was durably persisted before labels.

## Technical strength

The prediction dataclass is frozen, records are held in a tuple, the complete payload is self-hashed, and factory identity plus replay validation is required immediately before the label loader checks or opens the label file. The one-shot authoritative entrypoint is sequential and exposes no result-driven callback. The frozen result-integrity audit found zero post-freeze mutation.

The freeze is nevertheless shallow: each record is an ordinary mutable dictionary. There is no explicit `PREDICTION_FROZEN` state machine, consumed one-shot label-reader capability, atomic pre-label file write/reopen, process boundary, or post-label byte-equality check.

## Classification

`SAFE_BUT_WEAKER_THAN_D0_D2`

No verified leakage was found. The gap is governance strength, not evidence that labels changed the frozen prediction.

## Future recommendation

For a future independent D1 validation, atomically persist and replay the prediction before labels, require an explicit frozen state before the label reader can run, and verify the same bytes again after label processing. Do not retrofit or replace the frozen pilot result.
