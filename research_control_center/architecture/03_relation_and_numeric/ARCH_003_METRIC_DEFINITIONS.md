# ARCH-003 Metric Definitions

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Source parameter derivation

| Name | Definition | Unit | Purpose | Source symbol |
|---|---|---|---|---|
| Source noise scale | `max(1.4826 * MAD(file-local first differences pooled across train1/train2), 1e-12)` | source unit per row | Defines nontrivial changes and later step parameters | `multi_file_robust_scale_v1` |
| Nontrivial amplitude | `abs(median(x[t:t+5]) - median(x[t-5:t]))`, retained when strictly above source noise | source unit | Supplies the normal amplitude distribution | `derive_multi_file_source_parameters_v1` |
| Source step threshold | `max(5 * source_noise_scale, Q75_linear(nontrivial amplitudes))` after at least 20 amplitudes | source unit | Event threshold; equality passes during extraction | `derive_multi_file_source_parameters_v1` |
| Source stability tolerance | `max(3 * source_noise_scale, 0.10 * source_step_threshold)` | source unit | Bounds samples around pre/post medians | `derive_multi_file_source_parameters_v1` |
| Target noise scale | Same robust first-difference scale, once per target | target unit per row | Classifies response direction and normalizes effect | `derive_multi_file_target_scale_v1` |

## Event and response evidence

| Name | Formula or algorithm | Unit | Threshold/use | Source symbol |
|---|---|---|---|---|
| Source event | Complete 5-row pre/post medians; absolute delta at least step threshold; at least 4/5 samples stable on each side | event | Direction is sign of post-minus-pre | `extract_sustained_step_events_v1` |
| Refractory cluster | Same-source, file-local single-link clusters with successive gaps at most 10 rows; retain largest absolute step, earliest on tie | event | Deduplicates nearby detections | `cluster_step_events_v1` |
| Cross-source isolation | No retained event from another approved source within inclusive `t +/- 2` rows | event | Keeps isolated source contexts | `classify_event_isolation_v1` |
| Target response | `median(y[t+h:t+h+3]) - median(y[t-5:t])` | target unit | `h` in 1, 5, 10, 30, 60 rows; incomplete response is right-censored | `_direction_statistics` |
| Directional match | response strictly above target scale for increase, or strictly below negative target scale for decrease | Boolean | Neutral closed interval matches neither direction | `_direction_statistics` |

## Selection and confirmation metrics

| Metric | Exact definition | Fit threshold | Confirmation threshold |
|---|---|---:|---:|
| Support | Count of isolated, chosen-source-direction events with a complete target response window | total >= 20; train1 >= 5; train2 >= 5 | train3 >= 5 |
| Directional consistency | selected-direction matches divided by usable responses; pooled consistency uses summed matches/summed usable | pooled >= 0.70; each file >= 0.60; selected must strictly exceed opposite in each file | >= 0.60 and selected strictly exceeds opposite |
| Robust effect ratio | absolute median response divided by fixed target noise scale | >= 2.0 using pooled train1/train2 responses | >= 1.0 using train3 responses |

All gates are conjunctive. Fit selection occurs before the fit gate; a rejected winner does not fall back to a lower-ranked direction/horizon. Confirmation tests only the frozen winner and does not search or retune.

“Seconds” are implemented as row offsets under the frozen one-second sampling contract. The profiler does not independently parse timestamp continuity.

