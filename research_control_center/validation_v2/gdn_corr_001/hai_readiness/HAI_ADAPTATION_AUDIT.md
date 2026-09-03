# HAI GDN 설계 적합성 감사

- EXP-01B-V1은 raw 37-feature global MSE와 5-row history→next-row 예측을 사용했다.
- 정상 train1/train2 scale audit 결과 raw global MSE scale-dominated: `True`.
- 동결된 선택 규칙에 따른 EXP-01C preprocessing: `TRAIN_ONLY_ROBUST_MEDIAN_IQR`.
- 기존 validation은 모든 9개 run에서 train/validation raw timestamp가 겹쳤고, combined seed 11 block은 file boundary를 넘었다.
- EXP-01C는 file별 contiguous block, purge 66, raw overlap 0을 요구한다.
- EXP-01C는 horizons 1/5/10/30/60의 three-row future median을 공동 learned graph로 예측한다.
- Shared-encoder attention은 horizon별로 결속해 보고하되 head-specific attention으로 부르지 않는다.
- learned Top-5 graph member는 direct EdgeMask, 비회원은 NOT_IN_LEARNED_GRAPH 상태와 source occlusion 경로를 갖는다.
- 모든 결론은 normal-only predictive/functional evidence이며 causal claim이 아니다.
