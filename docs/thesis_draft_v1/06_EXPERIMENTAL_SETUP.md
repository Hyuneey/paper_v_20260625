# 5. 실험 설정

## 5.1 Dataset과 process

| 항목 | 설정 |
|---|---|
| Dataset | HAI 23.05 |
| Primary process | P1 Boiler |
| sampling | 1초 |
| candidate discovery | META / STAT / upstream-aligned GDN |
| initial universe | 144 directed source–target pairs |
| integrated cohort | 47 unique pairs |
| confirmed relations | 23 pairs, 42 directed relations |
| utility portfolio | COMMON-42 |
| INNER attack events | 14 |

원시 데이터는 Git 밖에 있으며 이 초안 작성에서는 읽지 않았다. 결과와
설정은 canonical remote checkpoint의 공개 frozen artifact에서 인용한다.

## 5.2 Split 역할

| 역할 | 사용 목적 | label 사용 |
|---|---|---|
| normal train1/2 | candidate/stat/GDN, relation fit, D0 model fit | 없음 |
| normal train3 | one-way relation confirmation, D0 threshold calibration | 없음 |
| normal train4 | normal guard/sanity | 없음 |
| test1 | label-blind D0/D1/D2 prediction | prediction 단계 없음 |
| label-test1 | prediction freeze 이후 INNER metric | 있음, metric 전용 |
| test2 / label-test2 | held-out OUTER | 읽지 못함 |

## 5.3 Rule construction 비교

| Arm | 구성 방식 | 비교 통제 | 동결 결과 |
|---|---|---|---|
| T0 | deterministic template | 동일 evidence/schema/verifier | 42/42 COMMON |
| T1 | one-shot constrained LLM | 동일 provider/model policy | 42/42 equivalent |
| T1-B | independent generations | T2와 동일 총 call budget | 42/42 equivalent |
| T2 | bounded verifier feedback | revise/retrieve/no_rule | 39 accepted, 3 no_rule |

이 비교는 agentic feedback의 performance superiority를 확정하지 않는다.

## 5.4 D0 reference detector

D0는 `D0_PCA_SPE_V1`이다. P1의 37개 feature를 normal-only fit/calibration에
사용한다. population mean/std(ddof=0)로 standardization하고 cumulative
explained variance가 0.95 이상인 최소 component 수를 선택한다. frozen
training 결과는 k=10이다. residual SPE score의 normal calibration
0.999 quantile을 threshold로 두며 equality는 alarm이 아니다. smoothing,
point adjustment, temporal dilation, test tuning은 없다.

D0는 제안 기여가 아니라 규칙 보완성을 평가하기 위한 reference detector다.

## 5.5 Metric

Primary metric은 Attack-event Recall과 Normal FAR episodes/hour다. attack
event는 strict label-one maximal contiguous run이고, alarm episode는 중복을
제거한 1초 point alarm의 maximal contiguous run이다. point adjustment는
하지 않는다. normal exposure는 51,019초이고 attack event는 14개다.

추가 metric은 D0-missed attack recovery rate, incremental attack-event
recall, added normal rule-recovery FAR/hour, incremental normal FAR/hour다.

## 5.6 Hyperparameter provenance 요약

| Parameter | 값 | 분류 | 해석 |
|---|---:|---|---|
| candidate Top-K | primary 20; view 10/20/40 | REASONABLE_BUT_SENSITIVITY_UNTESTED | bounded budget, 최적값 아님 |
| relation horizons | 1/5/10/30/60초 | REASONABLE_BUT_SENSITIVITY_UNTESTED | protocol 고정 grid |
| source refractory | 10초 | REASONABLE_BUT_SENSITIVITY_UNTESTED | 중복 event 연결 |
| isolation radius | ±2초 inclusive | REASONABLE_BUT_SENSITIVITY_UNTESTED | 다른 source 전이 오염 억제 |
| fit support | pooled≥20, each≥5 | FROZEN_AND_SUPPORTED | 최소 정상 근거 |
| fit consistency/effect | 0.70/0.60, ratio≥2.0 | REASONABLE_BUT_SENSITIVITY_UNTESTED | 방향·효과 gate |
| confirmation | support≥5, consistency≥0.60, ratio≥1.0 | FROZEN_AND_SUPPORTED | one-way train3 확인 |
| PCA variance | 0.95 | REFERENCE_BASELINE_ONLY | detector baseline choice |
| PCA selected k | 10 | FROZEN_AND_SUPPORTED | normal fit 결과 |
| D0 quantile | 0.999 | REFERENCE_BASELINE_ONLY | baseline FAR/recall 민감 |
| D2 source count | 2 | STRUCTURAL_LIMITATION_OBSERVED | 최소 non-singleton gate |
| D2 V1 time | exact same-second | STRUCTURAL_LIMITATION_OBSERVED | 비동기 signal 손실 |
| D2 V2 time | native horizon persistence | STRUCTURAL_LIMITATION_OBSERVED | recovery 없이 FAR 증가 |

사전 고정은 leakage 방지와 재현성 근거이지 최적성 증명이 아니다. 전체
provenance register는 논문 부록으로 이동한다.

## 5.7 평가 범위

INNER 결과는 14개 event에 대한 기술적 evidence다. 통계적 superiority,
held-out generalization, production deployability를 검정하지 않는다. OUTER는
data-custody boundary에서 feature byte read 전에 중단됐으므로 결과가 없다.
