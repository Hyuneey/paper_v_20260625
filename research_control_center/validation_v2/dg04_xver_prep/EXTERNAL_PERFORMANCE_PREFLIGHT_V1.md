# 외부 정상 실행 성능 사전 점검

상태: STATIC_REVIEW_COMPLETE / REAL_NORMAL_PREFLIGHT_BLOCKED_BY_CUSTODY.
HAI23 학습·checkpoint·환경은 변경하지 않았습니다. 외부 GDN 실행 0/12입니다.

1. 공식 normal-file identity replay 후 timestamp+feature 전용 bounded-memory projection/cache가 필요합니다.
   현재 label-free-only V1 guard는 정상 파일의 embedded label schema에서 fail closed합니다.
2. 37-node 전체 feature mapping과 version/split/cache hash를 먼저 고정해야 합니다.
3. train1-only/train2-only 각 11/23/37, 버전당 6개 run. Robust train-only scaler, purged validation,
   self-excluded shared graph, 1/5/10/30/60 heads, 고정 CUDA dtype/seed를 run1 전에 동결합니다.
4. 기존 generic training/window/streaming hash 구현을 재사용하되 HAI23 row-count·37-column 상수
   adapter를 외부 데이터에 직접 쓰지 않습니다. GDN train4 evidence와 global EdgeMask를 split-pure
   event-conditioned evidence로 잘못 표시하지 않습니다.
5. 동일 split의 event-conditioned extraction, immutable evidence cache, deterministic serialization,
   per-run atomic checkpoint resume, bounded graph-mask batching을 사용하고 reference 동등성 검증 후 실행합니다.
6. 실제 정상파일 performance 동등성·GPU smoke·환경 freeze는 custody 다음 단계이며 완료로 표시하지 않습니다.

eTaPR 성능은 별도 synthetic conformance receipt의 fixture별 측정값에만 해당합니다. 실행 시간 예측 없음.
