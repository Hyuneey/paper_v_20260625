# EXP-01C GDN HAI 결과

- Disposition: `LEARNED_GRAPH_SUPPORTING`
- Preprocessing: `TRAIN_ONLY_ROBUST_MEDIAN_IQR`; file-local purge 66; raw overlap 0.
- META+STAT / augmented confirmed yield@29: 21 / 20
- META+STAT / augmented NDCG@29: 0.776893 / 0.739170
- Stable positive event-conditioned EdgeMask pairs: 2
- GDN-unique Formal V4 convertible pairs: 0
- Shared-encoder attention은 `1/5/10/30/60`초 horizon에 동일 근거로 결속되며 head-specific attention이 아니다.
- Attention capture prediction invariance 및 checkpoint 불변성은 9/9 run에서 확인됐다.
- Evidence is normal-only predictive/functional evidence, not causal or physical ground truth.
- EXP-01B-V1 remains immutable; no test1, labels, test2, held-out, or provider input was used.
