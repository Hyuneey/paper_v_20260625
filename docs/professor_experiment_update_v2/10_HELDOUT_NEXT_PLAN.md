# DG04-XVER-PREP-001 — 현재 중단 지점

DG-04는 DEC-025 APPROVED_WITH_SCOPED_AGENTIC_CLAIM으로 고정했습니다. EXP-03B는 DG-03B_REVISED 승인 후 실행·QA 완료된 역사적 결과입니다. T2의 Agentic 의미 유도 이점은 matched-maximum-budget T1-B 대비이며 T0 우월성을 뜻하지 않습니다.

T0 14 pair/22 guard-retained Rules, T2 Repeat 1 13 pair/21 Rules를 별도 HELDOUT_CANDIDATE로 고정했습니다. V2A 21 pair/39 Rules 및 기존 EXP03B/EXP02/EXP04/05/PILOT 결과는 불변입니다.

Stage B: BLOCKED_NORMAL_DATA_CUSTODY. 공식 HAI22/21 train1 정상 컨테이너 각각의 byte identity 검증 후 embedded label schema에서 guard가 중단했습니다. label 값의 해석·검증·과학 사용은 0입니다. 전체 normal container hashing/decompression은 수행했으므로 label-bearing byte traversal 0이라고 주장하지 않습니다.
추가 정상 header 검사가 자동 보안심사에서 label 접근으로 거절되어 우회하지 않았습니다. 정상 schema에서 label 열만 식별하고 값은 버린 뒤 timestamp/feature만 투영하는 범위의 명시적 확인이 필요합니다. 사용자에게 로컬 경로나 upload를 요구하지 않습니다.

공식 표 기준 HAI22 24개, HAI21 22개 P1 역할 feature 대응; portable META 20/19. 정상 schema·sampling은 미검증이며 full GDN model mapping도 미완료입니다. 외부 STAT/GDN/T0 실행 및 T2 evidence pack 생성은 0입니다. DG-03C N/token/cost는 UNKNOWN이므로 아직 승인 가능한 provider brief가 아닙니다.

eTaPR 파일별 공식/합성 109건 정확 일치. 여러 파일의 버전 내 집계, P1 secondary range scope, empty-input 관례는 후속 metric 계약에서 해결해야 합니다. 실제 eligibility 0건, provider/credential/공격 payload 0입니다.

초기 read-only agent 공개 매뉴얼 검색에 scenario 설명이 일부 포함되었지만 공격 CSV/label file은 열지 않았고 eligibility/결과 판단에 사용하지 않았습니다.
Stage A만 QA PASS이며 전체 task PASS가 아닙니다. 부분/차단 상태는 validation-v2에 merge/push하지 않습니다. 교수 package는 초안이며 제출하지 않았습니다.

## 이전 상태 — 역사적 기록

# DG04-XVER-PREP-001 — 현재 승인된 방법 고정

DEC-025 / DG-04: APPROVED_WITH_SCOPED_AGENTIC_CLAIM. 제목: Verifier-Guided Agentic Relational Rule Induction with GDN-Based Learned-Graph Evidence for Explainable Multivariate Time-Series Anomaly Detection

동결 정상-only EXP-03B에서 T2는 matched-maximum-budget T1-B 대비 의미적 유도를 개선했지만 주요 지표에서 T0보다 우수하지 않았습니다. GDN은 핵심 learned-graph evidence 모듈이며 후보·탐지·수치 권한이 아닙니다. Fusion은 기여가 아닌 사전등록 비교입니다.

T0 단일 출력 및 T2 Repeat 1의 기존 guard-retained Rule만 별도 HELDOUT_CANDIDATE로 고정했습니다. V2A39 reference·EXP03B·EXP02·EXP04/05·PILOT 결과는 보존합니다. Stage B는 HAI22/21 정상-only 준비 중이며 provider는 DG-03C, 공격은 DG-05, 교수 제출은 DG-06 별도 승인입니다. 추가 Agentic rescue 없음.

## 이전 기록 — 역사적 상태

# Held-out 및 외부 버전 평가 다음 계획

현재 held-out 일반화는 미확인입니다. old OUTER는 custody check에서 byte read 전에 중단되었고 단순 재시도 권한은 없습니다. 기존 HAI 23.05 test1의 14개 시나리오는 개발 결과를 산출하기에는 유용하지만 최종 Recall의 정밀도와 버전 일반화를 주장하기에는 부족합니다. 하나의 공식 시나리오 안에 있는 attack interval이나 intervention을 독립 공격처럼 나누어 수를 늘리지 않습니다.

## 버전별 panel

- HAI 23.05 test1: 기존 14개 시나리오의 `DEVELOPMENT_ONLY` 결과를 그대로 보존하며 다시 열지 않습니다.
- HAI 23.05 test2: 38개 명목 시나리오의 `PRIMARY_HELDOUT` panel입니다.
- HAI 22.04: 58개 명목 시나리오의 `EXTERNAL_VERSION_REPLICATION_1`입니다.
- HAI 21.03: 50개 명목 시나리오의 `EXTERNAL_VERSION_REPLICATION_2`입니다.

비개발 panel의 명목 합계는 146개이지만 동일 분포의 IID 표본으로 간주하지 않습니다. 주 결과는 버전별 P1-eligible Scenario Recall과 정상 false episodes/hour로 분리 보고합니다. eTaP/eTaR/eTaPR F1, scenario coverage, time-to-first-detection, delay, alarm duration, overlap과 incremental FAR는 보조 지표입니다. 하나의 pooled Recall은 주 결과로 사용하지 않습니다.

## 공격 자료 접근 전에 고정할 것

1. panel별 study identity와 preregistration
2. 공식 scenario authority와 outcome-blind P1 eligibility authority
3. 버전별 data/split identity와 normal-only method re-instantiation
4. 최종 method·authority·feature·numeric policy
5. detector와 기존 frozen fusion policy
6. 공식 eTaPR source/parameter와 range conversion
7. durable prediction-before-label gate와 one-shot label lease
8. no-post-result-tuning 및 버전별 reporting plan

DG-05 승인 전에는 test2나 외부 버전 attack payload 및 label을 열지 않습니다. HAI 22.04/21.03은 같은 Rule bytes를 복사하지 않고 각 버전의 정상 데이터만으로 같은 방법을 다시 인스턴스화합니다.
