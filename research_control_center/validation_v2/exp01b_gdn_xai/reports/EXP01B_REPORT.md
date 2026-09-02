# EXP-01B GDN Prediction-XAI 결과

## 결론

EXP-01B는 사전등록된 정상 데이터 전용 비교를 완료했으며, 동결된 판정 규칙에 따라
`GDN_ABLATION_ONLY`로 귀결되었다. 이는 GDN이 일반적으로 무용하다는 뜻이 아니라,
이번 HAI 23.05 P1 정상 관계 참조와 동일 예산 비교에서 primary augmentation 또는
supporting evidence 요건을 충족하지 못했다는 뜻이다.

## 실행 경계

- 실험 ID: `EXP-01B-GDN-XAI-V1`
- backend: 별도 CUDA 환경, RTX 5060 Laptop GPU
- 실행: 3개 view × seed 11/23/37 = 9회
- 학습 입력: normal train1/train2
- 정상 관계 참조: train1/train2 profiling 후 train3 arm-blind confirmation
- 기능 검증: 고정 checkpoint와 normal train4
- test1, label, test2, held-out, provider 접근: 모두 0
- 기존 EXP-01과 PILOT V1: 변경 없음

## 정상 관계 참조

전체 144개 source→target pair를 동일한 arm-blind 정상 관계 절차로 평가했다. 그 결과
37개 pair와 65개 방향 관계가 normal-confirmed relation reference에 포함되었다. 이는
물리적 ground truth나 인과 그래프가 아니다.

## 동일 예산 결과

주 판정 예산은 META+STAT union과 같은 K=29이다.

| 비교 | confirmed pair yield | NDCG |
|---|---:|---:|
| META+STAT | 20 | 0.7427828733 |
| META+STAT+GDN Functional-Consensus | 21 | 0.7628608206 |

결합 순위는 combined view에서 yield와 NDCG가 소폭 증가했다. 그러나 TRAIN1_ONLY와
TRAIN2_ONLY의 비열화 조건을 모두 만족하지 못했으며, GDN 고유 confirmed pair 3개 중
Formal V4 executable rule로 변환된 pair는 0개였다.

## 기능적 근거

- attention capture: `AVAILABLE_INVARIANCE_PASS`
- combined-view EdgeMask가 matched random보다 큰 seed: 3개 중 2개
- primary Top-K EdgeMask median이 양수인가: 아니오
- 2개 이상 seed에서 양의 EdgeMask를 보인 안정적 GDN 고유 pair: 0
- 2개 이상 seed에서 양의 EdgeMask를 보인 안정적 META/STAT pair: 0

Attention weight와 EdgeMask는 예측 모델 내부의 관계·민감도 근거이며 인과성을
증명하지 않는다. Source occlusion은 file-local normal-distribution-preserving robustness
분석으로만 사용했다.

## 판정

`GDN_PRIMARY_AUGMENTATION` 조건은 split 안정성, 고유 executable rule, 양의 median
EdgeMask 요건에서 실패했다. `GDN_SUPPORTING_EVIDENCE`의 세 대안 조건도 충족하지
못했다. 따라서 V2 primary candidate authority는 V2A META+STAT을 유지하며, V2B primary
portfolio는 생성하지 않는다.

## 주장 경계

말할 수 있는 것:

- EXP-01B의 combined K=29 순위는 META+STAT 대비 정상-confirmed yield와 NDCG가 소폭 높았다.
- 그러나 동결된 안정성·기능·rule-conversion 기준을 통과하지 못해 GDN은 ablation으로 남았다.

말할 수 없는 것:

- GDN이 causal relation 또는 물리적 ground truth를 발견했다.
- GDN이 일반적으로 효과가 없거나, 반대로 성능을 검증했다.
- test1 탐지 성능이나 held-out 일반화를 개선했다.
