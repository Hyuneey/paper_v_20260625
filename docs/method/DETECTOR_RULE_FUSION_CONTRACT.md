# Detector-Rule Fusion Contract

## Predeclared arms

- `rule_only`
- `detector_only`
- `argos_fn_union`
- `argos_fp_intersection`
- `confidence_gated_correction`
- `abstention_aware_fusion`

No arm is assumed superior.

## ARGOS-style baselines

For aligned binary labels:

```text
argos_fn_union = max(detector_binary, rule_binary)
argos_fp_intersection = min(detector_binary, rule_binary)
```

These are behavioral baselines from the ARGOS audit. They require frozen
detector and rule artifacts and do not establish that either correction helps.

## Confidence-gated correction specification

- Detector input: aligned binary label plus optional calibrated score, artifact
  hash, detector version, and validation-frozen operating threshold.
- Rule input: accepted rule binary/score/abstention output, rule/verifier hashes,
  and approved parameter provenance.
- Confidence provenance: validation-only calibration record for both detector
  and rule signals; no raw provider confidence.
- Gate threshold provenance: selected on validation under a pre-registered
  metric and frozen before test.
- Conflict handling: apply only the predeclared correction direction when both
  inputs are available and the correction confidence passes the frozen gate;
  otherwise retain detector output.
- Rule abstention: detector output remains unchanged.
- Detector unavailable plus rule abstention: fused output abstains.
- Both available but unsupported regime: abstain or retain detector according
  to the frozen arm, never decide after test inspection.

## Evaluation policy

Fusion selection and thresholds use validation only. Detector, rule, gate,
threshold, and alignment hashes are frozen before one-way test evaluation.
Primary reporting is PA-free. Point-adjusted and ARGOS Event-PA metrics are
supplementary and cannot select the proposed method.
