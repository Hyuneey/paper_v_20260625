# Hyperparameter/code cross-check

The professor register was compared with the remote configs and frozen public
authorities. No value or semantic mismatch was found.

| Parameter | Remote value/semantics | Classification |
|---|---|---|
| candidate Top-K | primary 20; views 10/20/40; no padding | REASONABLE_BUT_SENSITIVITY_UNTESTED |
| relation horizons | 1/5/10/30/60 seconds | REASONABLE_BUT_SENSITIVITY_UNTESTED |
| source refractory | 10 seconds | REASONABLE_BUT_SENSITIVITY_UNTESTED |
| cross-source isolation | ±2 seconds inclusive | REASONABLE_BUT_SENSITIVITY_UNTESTED |
| fit support | pooled ≥20; each train ≥5 | FROZEN_AND_SUPPORTED |
| fit consistency | pooled ≥0.70; per-file ≥0.60 | REASONABLE_BUT_SENSITIVITY_UNTESTED |
| fit effect ratio | ≥2.0 | REASONABLE_BUT_SENSITIVITY_UNTESTED |
| calibration support | ≥5 isolated events | FROZEN_AND_SUPPORTED |
| calibration consistency/effect | ≥0.60 / ≥1.0 | REASONABLE_BUT_SENSITIVITY_UNTESTED |
| PCA retained variance | 0.95 | REFERENCE_BASELINE_ONLY |
| frozen selected PCA k | 10 | FROZEN_AND_SUPPORTED |
| D0 threshold quantile | 0.999, strict `score > threshold` | REFERENCE_BASELINE_ONLY |
| D2 source requirement | 2 distinct sources; same-source duplicates count once | STRUCTURAL_LIMITATION_OBSERVED |
| D2 V1 temporal policy | exact decision-second equality | STRUCTURAL_LIMITATION_OBSERVED |
| D2 V2 temporal policy | causal inclusive persistence through each rule's native horizon | STRUCTURAL_LIMITATION_OBSERVED |

The register correctly distinguishes preregistration/audit from sensitivity.
No tuning is implied, and the D2 entries accurately describe a structural
mismatch rather than an optimized policy.
