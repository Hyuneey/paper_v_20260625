# XVER-T2 — 외부 버전 정상-only 포트폴리오 동결 완료

XVER-T2-PROVIDER-EXEC-001: COMPLETE_NORMAL_ONLY / QA PASS.
정확한 snapshot gpt-5.4-mini-2026-03-17로 HAI22 61회, HAI21 61회, 합계 122회 호출했습니다. retry/fallback/tools/4차 호출은 0이며 EVENT10은 전송하지 않았습니다.
실제 계량 사용량은 입력 333954 / 출력 13563 / 합계 347517 tokens이고 표준 공개가격 단순 산식은 USD 0.311499입니다. 이는 청구서가 아닙니다.
HAI22 T2는 train2 입장 20 pairs, 정상 확인 31 Rules, Formal V4 31, train4 유지 19 Rules/16 pairs입니다.
HAI21 T2는 train2 입장 18 pairs, 정상 확인 9 Rules, Formal V4 9, Block B 유지 2 Rules/1 pairs입니다.
두 결과는 HELDOUT_CANDIDATE이며 공격 검증·production·T2>T0 일반화 결론이 아닙니다. T0/T2/V2A는 별도 사전등록 방법으로 유지하며 선택하지 않았습니다.
모든 provider 출력과 admission을 양 버전에서 먼저 닫은 뒤 train3/Block A, SCI02B, Formal V4, 단방향 guard를 수행했습니다. 공격/test/label/real eligibility 접근은 0입니다.
DG-XVER-PROVIDER는 승인·실행 완료. DG05는 NOT_APPROVED, 교수 package는 NOT_SUBMITTED, DG06 필수입니다.
정확한 다음 작업은 MULTIPANEL-PRE-DG05-FREEZE-001이며 multi-file aggregation, empty-input, secondary P1 해석과 최종 prediction-before-label custody를 공격 접근 전에 고정합니다. 백업은 SINGLE_COPY_LOCAL_ONLY입니다.

## 이전 기록 — 역사적 상태

# HAI-XVER — 정상-only 실행 완료 / Provider 승인 대기

HAI-XVER-NORMAL-PREP-001: 정상-only 실행 완료, 독립 최종 QA PASS. DG-XVER-PROVIDER에서 정지합니다.
HAI22/HAI21 GDN은 각각6회, 총12회입니다. GLOBAL5는 train1 provider / train2 retrieval, EVENT10은 보조 분석 전용이며 융합·후보·verifier·T0·숫자·guard 사용을 금지합니다.
HAI22 T0: 13 Rules/12 pairs. HAI21 T0: 7 Rules/5 pairs. 모두 HELDOUT_CANDIDATE, 공격 검증·production 결과가 아닙니다.
T2 provider/retrieval packs와 정확 예산은 버전별 고정됐습니다. 합계 최대 174 calls, 3622912 tokens, 표준 공개가격 상한 USD 4.06이며 실제 지출이 아닙니다.
DG-XVER-PROVIDER는 USER_DECISION_REQUIRED; provider/credential/공격 접근0. DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; DG06 필수.
DEC025 제목·claim·HAI23 V2A/T0/T2·EXP03B·EXP02·EXP04/05·PILOT 결과 불변. T2>T1-B는 정상 의미 유도에 한정하며 T0보다 우수하지 않습니다.
후보 권한 META+STAT, GDN은 비인과적 learned-graph evidence, SCI02B 고정 숫자 결합, FormalV4 실행권한, guard 단방향. 37정책 재선택·META 재구성·best seed 없음.
eTaPR109 합성/가상 동등성 PASS. 다중파일/empty/secondary P1 해석은 DG05 전 결정 항목으로 유지하며 실제 eligibility는 생성하지 않았습니다. 백업 SINGLE_COPY_LOCAL_ONLY.

## 이전 기록 — 역사적 상태

# HAI-XVER — 승인된 GDN GLOBAL / AUX EVENT 역할 분리

HAI-XVER-NORMAL-PREP-001: APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES.
이전 BLOCKED_GDN_METHOD_CHANGE_REQUIRED의 estimator 역할 선택은 사용자 승인으로 해소됐습니다.
Provider train1 / bounded retrieval train2에는 EXP03B-compatible split-pure GLOBAL 5-row GDN만 사용합니다.
SCI01 split-local event와 seed별 purged validation 교집합의 EVENT 10-row는 AUXILIARY_CORROBORATION_ONLY입니다.
Global/event 융합, event의 provider·retrieval·verifier·candidate 사용, train3/4 또는 numeric policy 기반 event 선택을 금지합니다.
3개 seed 전부 유지; best-seed 선택 없음. 별도 타입과 실제 frozen projector adapter 합성검사 15 PASS 및 독립 scoped QA PASS.
과학적 역할 binding은 완료됐지만 버전별 execution adapter·custody·environment·performance preflight 통합은 남아 있습니다.
현재 GDN scientific runs 0/12, 외부 T0·T2 pack·정확 token/cost 미완료; provider/credential/공격0.
기존 DEC-025와 Stage A / V2A39 / T0 22 / T2 Repeat1 21 Rules / EXP03B / EXP02 / EXP04/05 / PILOT 결과는 불변입니다.
T2 > T1-B는 정상-only 의미 유도 비교에 한정되고 T0보다 우수하지 않습니다.
DG-XVER-PROVIDER NOT_READY_EVIDENCE_PENDING; DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; vault SINGLE_COPY_LOCAL_ONLY.

## 이전 기록 — 역사적 상태

# HAI-XVER-NORMAL-PREP-001 — context PASS / 과학 binding 필요

HAI-XVER-NORMAL-PREP-001: context 준비 PASS, BLOCKED_GDN_METHOD_CHANGE_REQUIRED.
부모 Stage A / DEC-025 / V2A39 / T0 22 / T2 Repeat1 21 Rules는 불변입니다.
T2 > T1-B는 동결된 정상-only 의미 유도 비교에 한정되며 T0보다 우수하지 않습니다.
HAI22 GDN context36/37, HAI21 30/37: 정확한 ordered intersection, 가변 node CUDA 합성검사 PASS.
Context train1/train2 positive allowlist projection은 버전별2개 완료; excluded label 값 파싱0.
기존 EXP01C event masking은 확정 relation·pooled threshold·train4를 사용하고 EXP03B는 global validation masking입니다.
Split-pure event-conditioned provider estimator의 threshold/window/direction 집계 정의를 새로 승인·동결해야 합니다.
따라서 과학 GDN0/12, 외부 T0·T2 pack·정확 token/cost 미완료. Provider/credential/공격0.
DG-XVER-PROVIDER는 NOT_READY, DG05 NOT_APPROVED, 교수 package NOT_SUBMITTED, vault SINGLE_COPY_LOCAL_ONLY.

## 이전 기록 — 역사적 상태

# DG04-XVER Stage B 재개 — 정상 custody 완료

DG-04 / DEC-025와 Stage A는 불변입니다. DG-03B_REVISED 승인 후 동결된 EXP-03B에서 T2는 matched-budget T1-B 대비 이점이 있지만 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules, V2A39는 별도 authority입니다.

사용자 schema-only allowlist projection 승인으로 정상 custody 차단을 해결했습니다. HAI22 train1~6/HAI21 train1~3 모두 NORMAL_ONLY_CUSTODY_READY. Label 이름은 header metadata로만 관찰하고 값 decode·검증·사용0. META/STAT union은 각29pairs, GDN admission0입니다.

현재 BLOCKED_PENDING_HAI_XVER_NORMAL_PREP: external GDN context/evidence, T0, provider packs 미완료. DG-XVER-PROVIDER exact token/cost 미정, calls0. eTaPR per-file109 PASS; 세 metric binding은 공격 전 결정 필요. 공격·credential0, 제출/merge/push 없음.

HAI22: 24 exact role features(12×12); HAI21: 22 exact(11×11), P1_PP04/P1_TIT03 ABSENT. Alias 추정0.
META20/19와 STAT20/20의 deduplicated union은 모두29이며 no padding/재생성 없음.
HAI21 train3는 frozen p60/half-open A/purge/B 산술만 materialize; block scientific execution0.
GDN은 이번 task scientific runs0. P1_PP04D 등 full context 매핑 완료 후 기존 architecture family와
split-pure event-conditioned evidence를 별도 후속 task로 실행합니다. Provider budget 준비 완료가 아닙니다.
과거 BLOCKED_NORMAL_DATA_CUSTODY 기록은 보존하며 이번 DEC-026이 schema-only 접근을 승인합니다.
Label-bearing normal container byte traversal은 있지만 excluded values deserialization0입니다.
교수 package는 NOT_SUBMITTED, vault SINGLE_COPY_LOCAL_ONLY, DG05/DG06 별도입니다.


## 이전 상태 — 역사적 기록

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
