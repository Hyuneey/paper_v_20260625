# 외부 정상 성능 사전 점검

실측: 9개 streaming projection 완료, 기존 scalar/vectorized STAT synthetic parity PASS.
Projection은 byte framing만 전체 traverse, selected-only decode; 파일당 최대CSV record1MiB.
Projected CSV를 immutable shared cache로 재사용하고 float64 round_trip으로 frozen STAT 정밀도를 보존합니다.
Projection file별 wall_seconds는 custody receipts, STAT wall_seconds는 candidate receipts에 기록했습니다.

| 경로 | 병목 분류 | 고정 대응 |
|---|---|---|
| acquisition/hash/projection | IO_BOUND + PYTHON_OVERHEAD | streaming; selected spans; streaming hash; immutable reuse |
| timestamp/mapping | CPU_BOUND | once-per-projection validation; receipt lookup |
| STAT | CPU_BOUND + MEMORY_BOUND | unchanged vectorized matrix; one split at a time; scalar parity |
| temporal evidence/SCI02B/Formal V4/guard | CPU_BOUND/PYTHON_OVERHEAD | frozen kernels; cached tuples; source-specific event universe |
| GDN windows/training/extraction | GPU_BENEFICIAL + MEMORY_BOUND | future fixed CUDA; batch windows/masks; atomic per-run checkpoint |
| T0/hidden verifier/serialization | CPU_BOUND/PYTHON_OVERHEAD | immutable evidence cache; deterministic serialization |

GDN real run/smoke/environment verification와 외부 temporal/T0 guard는 아직 실행하지 않았습니다.
별도 후속 contract에서 reference equivalence 후 실행합니다. HAI23 backend/seed/hyperparameter 변경0.
실제 정상 결과로 성능 설정을 선택하지 않았습니다. 시간 예측 없음.
