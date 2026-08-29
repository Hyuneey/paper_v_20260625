# ARCH-007 Feature Contract

| Item | Audited contract |
|---|---|
| Dataset/process | HAI 23.05 / P1 Boiler |
| Feature count | 37 |
| Ordering | Frozen explicit `P1_FEATURE_ORDER`; canonical source-column order |
| Included | Every frozen P1-prefixed numeric field, including command/state-style fields |
| Excluded | timestamp, label, attack metadata, non-P1 fields |
| Numeric type | NumPy `float64` |
| Missing/non-finite | No imputation; malformed, missing, NaN, infinity, wrong shape or wrong dtype fails closed |
| Constant fields | Retained; scale receives the `1e-12` floor |
| Fit splits | normal train1 then normal train2, concatenated without shuffle |
| Prediction split | test1 features only; labels are in a separate later path |

The feature contract is not the 12-source by 12-target relation-role universe. D0 uses all 37 frozen P1 feature columns, whereas candidate discovery uses purpose-specific source and target roles.

Evidence: `task039e3_r2r_d0_detector_design_v1.py`, `_parse_normal_frame`, `_parse_test1_feature_frame_once_v1`, frozen feature-scope and model receipts.

