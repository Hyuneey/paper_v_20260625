# ARCH-008 D1 Evaluated Object

The evaluated D1 object is **COMMON-42 Verified Relational Rule-only**. It is not a direct T2 output.

| Item | Frozen identity or meaning |
|---|---|
| Portfolio | 42 `CanonicalRuleDescriptorV4` descriptors in COMMON-42 |
| Runtime authority | V4 evaluator bundle plus Utility V4 normal-only numeric resolver and committed one-attempt INNER grant |
| Evaluation split | HAI 23.05 P1 `test1`, INNER development pilot |
| Prediction object | `ScientificRulePredictionArtifactV1` |
| Opportunities | 6,031 automatically enumerated applicable relation opportunities |
| Rules | 42 descriptors |
| Prediction records | 6,031 rule-opportunity records |
| Alarm representation | `alarm_emitted=true` on an anomalous rule record at its decision row |
| Trace representation | task-specific compact record plus terminal trace hash; not canonical `RuntimeTraceV1` |
| Label boundary | prediction completed and validated in memory before label access; not durably written before labels |
| Metric consumer | `derive_attack_events_v1`, `form_alarm_episodes_v1`, event overlap and normal FAR interfaces |

The public prediction artifact binds its portfolio, runtime authority, descriptor, registry, feature, split, bridge and prediction hashes. It contains 788 anomalous rule records. Deduplicating their decision rows yields 630 alarm seconds; grouping consecutive alarm seconds yields 626 episodes. These are distinct populations.
