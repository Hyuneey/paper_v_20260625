# EXP-01 및 EXP-01B GDN 결과

## 기존 EXP-01

기존 EXP-01의 동결 결과는 변경하지 않았습니다. primary mask pair가 0개였고,
사전등록 판정에 따라 GDN은 ablation으로 강등되었습니다. 이에 따라 VALIDATION V2의
주 후보 탐색 경로는 `META_PLUS_STAT`으로 고정되었습니다.

## 교수님 피드백에 따른 GDN Prediction Model + XAI 추가 검증

기존 음성 결과를 지우거나 재해석하지 않고 별도 실험 `EXP-01B-GDN-XAI-V1`을
사전등록했습니다. corrected self-excluded GDN을 3개 view와 seed 11/23/37로 실행하고,
Embedding, Attention, EdgeMask, Source Occlusion 및 Functional-Consensus를 동일한
144-pair normal-confirmed relation reference에서 비교했습니다.

### 실행 경계

- train1/train2: GDN 학습과 후보 근거
- train3: arm-blind 정상 관계 확인
- train4: 고정 checkpoint 기능 검증
- CUDA 과학 실행: 9회
- test1, 공격 label, test2, held-out, provider: 접근 0

### K=29 동일 예산 결과

| 순위 | confirmed pair yield | NDCG |
|---|---:|---:|
| META+STAT | 20 | 0.7427828733 |
| META+STAT+GDN Functional-Consensus | 21 | 0.7628608206 |

combined view에서는 작은 개선이 관찰됐습니다. 하지만 TRAIN1_ONLY와 TRAIN2_ONLY에서
비열화 조건이 유지되지 않았고, GDN 고유 confirmed pair 3개 중 Formal V4 executable
rule로 변환된 pair는 0개였습니다. primary Top-K EdgeMask 중앙값도 양수가 아니었습니다.
EdgeMask가 matched random보다 큰 combined seed는 3개 중 2개였으나, 이것만으로
supporting evidence의 동결 조건을 충족하지 못했습니다.

### 최종 판정

동결된 3단계 판정 규칙의 결과는 `GDN_ABLATION_ONLY`입니다. 따라서 V2A META+STAT
portfolio를 유지하고 V2B primary GDN portfolio는 만들지 않습니다.

이 결과는 GDN이 일반적으로 무용하다는 뜻이 아닙니다. 이번 정상 데이터 범위에서
안정적·고유·기능적 contribution 요건을 통과하지 못했다는 뜻입니다. Attention과
EdgeMask는 모델 내부 예측 근거이며 인과 또는 물리적 ground truth로 해석하지 않습니다.

## 후속 EXP-01B-R1 / EXP-01C와 현재 GDN 역할

위 EXP-01B 수치는 원래 frozen protocol의 역사적 결과다. 평가 구현 문제와 별도 수정 분석은 GDN-CORR-001에서 분리했다.
Rule conversion과 ranking 문제를 고친 분석으로 과거 결과를 덮어쓰지 않았다.
이후 한 번의 HAI-adapted multi-horizon EXP-01C는 `LEARNED_GRAPH_SUPPORTING`으로 동결됐다.

현재 GDN은 주 후보 탐색 authority가 아니다. META+STAT의 29pair·39-rule V2A portfolio는 바뀌지 않았다.
정상 source-event-conditioned EdgeMask의 안정 양성 pair를 immutable evidence에서 읽어 V2A에 대응시킨 결과:
2pair 모두 pair+horizon 일치, pair-only 0, no-overlap 0이다.
COMBINED view의 2/3 이상 seed 조건이며 모든 split에서 안정하다고 주장하지 않는다.
예측 MSE의 기능적 의존 근거는 physical causality나 Rule response sign의 증명이 아니다.

GDN sidecar는 39-rule descriptor를 변경하지 않는 설명용 annotation이다.
실제 EXP-05 6,418개 설명 중 130개에만 승인된 GDN 문구가 붙었다.
제목 eligibility는 `GDN_ASSISTED_TITLE_STRONG`이지만 문서상 일치 기준일 뿐이다.
잠정 제목: “GDN-Assisted Evidence-Bound Relational Rule Construction for Explainable Multivariate Time-Series Anomaly Detection”.
최종 제목은 DG-04 결정 전까지 잠정이다.
