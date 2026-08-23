# INNER D2 V1/V2 Scientific Disposition

## 1. Experimental question

Did verified Rule-only complementarity translate into useful detector-preserving fusion?

## 2. Frozen results

| Arm | Recall | Normal FAR/h | D0 miss recovery | Role |
|---|---:|---:|---:|---|
| D0 | 0.7857142857142857 | 0.4939336325682589 | N/A | Detector baseline |
| D1 | 0.9285714285714286 | 40.50255787059723 | 3/3 potential | Rule-only |
| D2 V1 | 0.7857142857142857 | 0.7056194750975128 | 0/3 | Combined V1 |
| D2 V2 | 0.7857142857142857 | 6.915070855955625 | 0/3 | Combined V2 |

## 3. Detector-rule complementarity

D1 detected all three D0-missed INNER attack events; D0 and D1 jointly covered all 14 events. This supports complementary event information, not standalone operational utility, because D1 FAR was high.

## 4. Why D2 V1 failed

Its exact-same-second multi-source gate retained none of the known D0-miss recovery evidence and produced three normal recovery false alarms.

## 5. Why D2 V2 did not fix V1

Native-horizon memory increased corroboration activity, but D0-miss recovery remained 0/3 and normal FAR increased materially. Extending evidence over native temporal support did not resolve fusion utility.

## 6. V1 versus V2

Recall was equal, while V2 FAR was 9.799999999999999 times V1 FAR. V1 therefore Pareto-dominates V2 on the two frozen primary utility dimensions.

## 7. Stop further INNER tuning

Further policy search on the same INNER labels is closed to limit post-hoc overfitting. No D2 V3, window, threshold, whitelist, score gate, learned fusion, or test1 calibration is authorized.

## 8. Supported claims

- RULE_CONSTRUCTION_PRODUCES_EXECUTABLE_VERIFIED_RULES
- RULE_LAYER_DETECTS_ATTACK_EVENTS
- RULE_LAYER_HAS_DETECTOR_COMPLEMENTARY_EVENT_INFORMATION
- D0_D1_EVENT_LEVEL_COMPLEMENTARITY_EXISTS_ON_INNER
- RULE_ONLY_HAS_HIGH_FALSE_ALARM_BURDEN
- D2_V1_DOES_NOT_IMPROVE_D0_ON_INNER
- D2_V2_DOES_NOT_IMPROVE_D0_ON_INNER
- NATIVE_HORIZON_MEMORY_DOES_NOT_SOLVE_FUSION_UTILITY_ON_INNER
- NEGATIVE_FUSION_RESULTS_ARE_REPRODUCIBLE_AND_INTEGRITY_AUDITED

## 9. Unsupported claims

- COMBINED_METHOD_IMPROVES_ATTACK_RECALL
- COMBINED_METHOD_REDUCES_FALSE_ALARMS
- RULE_ONLY_IS_OPERATIONALLY_DEPLOYABLE_AS_IS
- NATIVE_HORIZON_FUSION_IS_SUPERIOR
- D2_V1_IS_SUPERIOR_TO_D0
- D2_V2_IS_SUPERIOR_TO_D0
- CAUSAL_ROOT_CAUSE_IDENTIFICATION
- GENERALIZATION_TO_OUTER

## 10. Final combined candidate

D2 V1 is retained only as the simpler, lower-FAR, INNER Pareto-preferred combined candidate. It is not a successful combined method or proven improvement.

## 11. Proposed sealed OUTER evaluation

Preregister exactly D0 detector-only, D1 Rule-only, and D2 V1 combined. Freeze all designs and execute sealed test2 once, prediction-before-label, with no recalibration or redesign.

## 12. Exact next step

TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-PREREGISTRATION-AND-AUTHORIZATION-V1

OUTER remains unauthorized.

<!-- BEGIN D2 V1 V2 DISPOSITION REPORT PROVENANCE V1 -->
Report-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1
Report-Self-Hash: 4dfe4410d0b417895f5f03469dce69708c4ae3e340afeb1581d3785108d9b8fd
Bundle-Hash: 051d9b64988bd15b2e7d9b6b318ee5574896645f434a4a21f8940f1c6391efcf
Receipt-Hash: 4f670ed37aafaeaa7324b18fdae0272d6390bd9ad0e53b5a708207e06ed5e9cc
<!-- END D2 V1 V2 DISPOSITION REPORT PROVENANCE V1 -->
