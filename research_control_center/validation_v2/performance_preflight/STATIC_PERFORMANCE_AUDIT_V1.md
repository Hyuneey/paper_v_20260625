# 실행 전 성능 점검

## 범위

D0 PCA-SPE, Isolation Forest, 39-rule Formal V4 runtime, 두 confirm2 fusion, dense prediction custody, label gate, common metrics, 실제 trace 형태의 EXP05 renderer/fidelity를 합성 입력으로 점검한다. GPU 학습 작업이 아니므로 CPU_APPROPRIATE다. frozen model/config/data/seed/metric은 변경하지 않는다.

## 병목과 적용 범위

원래 per-opportunity 전체 authority 로딩 및 fsync를 반복하지 않도록 기존 prepared runtime을 한 번 연다. source/threshold/tolerance가 동일한 event scan은 캐시하고 frozen both-direction 다른 source event union을 재사용한다. 각 opportunity의 Formal V4 판정은 한 번만 수행한다. 두 fusion은 그 native outcomes와 frozen D1을 재사용한다.

EXP05는 원래 full unit schema를 유지한 최대 256-unit JSONL batch로 atomic write→fsync→close→reopen한다. 단위별 trace·explanation·fidelity hash는 사라지지 않는다. Batch는 provisional이고 authority 최종 replay 및 전체 census 일치 후에만 accepted receipt를 발행한다. Native coverage도 별도 frozen census에 결속한다.

기존 reference materializer와 합성 full-unit equality, cutoff/tail ABSTAIN, relation-local refractory, other-source union, mutation rejection을 검사한다. GDN sidecar는 outcome에 영향을 주지 않는다.

## 계측 해석

V1 profile은 초기 hardening 전 tracemalloc+cProfile snapshot이다. 390 trace 약38초, 1560 trace 약150–154초였지만 실제 실행 시간 예측이 아니다. 최종 V2 profile은 GDN annotation과 강화된 replay를 포함하고 loaded-source hashes를 시작/종료에 비교한다. cProfile만 사용하며 이전 allocation profile과 직접 속도 개선율을 계산하지 않는다. OS disk throughput 및 process RSS는 NOT_MEASURED로 명시한다.
