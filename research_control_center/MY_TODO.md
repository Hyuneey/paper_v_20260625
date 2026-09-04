<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=0679baf23b38ac292c9ec0334debce0277b7bbb1b7d17558ff90374c40286fe3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 내가 해야 할 연구 검토

## VALIDATION V2 개발 결과 · 결과 무결성 QA PASS

모든 5개 prediction freeze와 replay 후에만 test1 label을 해석했습니다.
PILOT V1과 별도 결과이며 최종 과학적 검증은 아닙니다.

| 방법 | Attack-event Recall | Normal FAR/hour | 정상 false episode |
|---|---:|---:|---:|
| D0 PCA-SPE | 11/14 | 0.4939336325682588839451968874340932 | 7 |
| Isolation Forest | 5/14 | 1.764048687743781728375703169407476 | 25 |
| Rule-only V2A | 11/14 | 37.60951802269742644896999157176738 | 533 |
| PCA+Rule | 11/14 | 0.6350575275877614222152531409866912 | 9 |
| IF+Rule | 5/14 | 1.905172582763284266645759422960074 | 27 |

두 고정 fusion은 추가 탐지 0개, 정상 false episode 각각 2개 증가로 탐지 개선이 지지되지 않았습니다.
전체 6,418개 actual trace의 자동 구조 충실도 QA는 PASS입니다.
GDN은 LEARNED_GRAPH_SUPPORTING: 2개 pair의 보조 근거이며 130개 설명에 선택적 문구를 붙였을 뿐 예측에는 영향을 주지 않습니다.
EXP-01·EXP-01B의 기존 음성 결과는 유지합니다. 전체 split에서 GDN 안정성을 입증한 것은 아닙니다.
14 contiguous attack-event units의 통계적 독립성, human usefulness, held-out 일반화는 미확인입니다.
평가 계획은 HAI23 test2 primary held-out와 HAI22/21 external replication으로 확대됐습니다.
146개 nominal scenario는 IID가 아니며 primary pooled Recall을 만들지 않습니다. 실제 P1 denominator는 아직 pending입니다.
다음: DG-XVER-PROVIDER. DG-03 provider 승인, DG-04 제목, DG-05 attack panel, DG-06 실제 제출은 서로 별도 Gate입니다.


이 문서는 낮은 수준의 개발 작업이 아니라 연구 책임자가 확인하거나 결정할 항목을 모은다.

## 결정 필요

현재 항목이 없습니다.
## 이해 필요

- **ID:** USER-V2-007
  **우선순위:** 중간 (MEDIUM)
  **할 일:** Fresh-machine PASS는 과거 synthetic 환경 재현에 한정된 근거로 읽는다.
  **사용자 확인이 필요한 이유:** 이번 과학 실행 코드의 새 환경 재현이나 private data 복원을 의미하지 않는다.
  **연결 문서:** research_control_center/validation_v2/reports/V2_FRESH_MACHINE_SYNTHETIC_REHEARSAL_RECEIPT.json
  **상태:** 미결정
## 검토 필요

현재 항목이 없습니다.
## Codex 작업 대기

현재 항목이 없습니다.
## 승인된 정책

- **ID:** USER-V2-001
  **우선순위:** P0
  **할 일:** DATA-POLICY-001 CODE_BASED_MATERIALIZATION으로 공식 HAI 23.05 normal 파일을 materialize하고 custody를 발급한다.
  **사용자 확인이 필요한 이유:** 네 normal split의 byte equivalence와 schema identity가 확인되어 custody가 발급되었다.
  **연결 문서:** research_control_center/validation_v2/receipts/HAI_NORMAL_ONLY_CUSTODY_BINDING_V2.json
  **상태:** 완료
## 보존 원칙

- **ID:** USER-V2-002
  **우선순위:** 높음 (HIGH)
  **할 일:** test1은 DEVELOPMENT_ONLY로만 해석하고 test2/heldout gate를 유지한다.
  **사용자 확인이 필요한 이유:** test1은 모든 prediction freeze 뒤에만 label을 해석했다. 최종 검증은 아니다.
  **연결 문서:** research_control_center/validation_v2/VERSION_POLICY.md
  **상태:** 미결정

- **ID:** USER-V2-008
  **우선순위:** 높음 (HIGH)
  **할 일:** PILOT V1과 이미 동결된 V2 결과를 그대로 보존한다.
  **사용자 확인이 필요한 이유:** 후속 연구는 별도 방법·authority·artifact·report ID가 필요하다.
  **연결 문서:** research_control_center/validation_v2/PILOT_V1_PRESERVATION_MANIFEST.json
  **상태:** 미결정
## 추후 결정

- **ID:** USER-V2-003
  **우선순위:** 높음 (HIGH)
  **할 일:** DG-03 고정 snapshot 승인·EXP-03 실행 완료
  **사용자 확인이 필요한 이유:** T0 39/39; T1 104/117; T1-B 115/117; T2 105/117
  **연결 문서:** research_control_center/validation_v2/exp03/execution_v1/EXP03_RESULTS_REPORT_V1.md
  **상태:** 완료

- **ID:** USER-V2-004
  **우선순위:** 높음 (HIGH)
  **할 일:** 정상 schema-only projection 승인·custody 복원 완료
  **사용자 확인이 필요한 이유:** DEC-026;9개 projection 비간섭 PASS
  **연결 문서:** research_control_center/validation_v2/dg04_xver_prep/STAGE_B_RESUME_STATUS_V2.json
  **상태:** RESOLVED
## 필수 향후 Gate

- **ID:** USER-V2-005
  **우선순위:** 높음 (HIGH)
  **할 일:** HAI23 test2·HAI22·HAI21 attack panel 첫 접근 전에 combined DG-05 package를 검토한다.
  **사용자 확인이 필요한 이유:** old OUTER를 재사용하지 않고 P1 eligibility·scenario authority·version별 prediction custody를 먼저 고정한다.
  **연결 문서:** research_control_center/validation_v2/evaluation_expansion/DECISION_GATE_PLAN_V1.md
  **상태:** 미결정
## 검토 필요

- **ID:** USER-V2-006
  **우선순위:** 높음 (HIGH)
  **할 일:** 실제 EXP04/05 결과가 포함된 교수님 package를 제출 전에 검토한다.
  **사용자 확인이 필요한 이유:** DG-06 전 이메일을 보내지 않는다.
  **연결 문서:** docs/professor_experiment_update_v2/01_ONE_PAGE_SUMMARY.md
  **상태:** 미결정

과학 source authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 현재 승인된 DG-04 및 실제 중단 지점

HAI-XVER-NORMAL-PREP-001: 정상-only 실행 완료, 독립 최종 QA PASS. DG-XVER-PROVIDER에서 정지합니다.
HAI22/HAI21 GDN은 각각6회, 총12회입니다. GLOBAL5는 train1 provider / train2 retrieval, EVENT10은 보조 분석 전용이며 융합·후보·verifier·T0·숫자·guard 사용을 금지합니다.
HAI22 T0: 13 Rules/12 pairs. HAI21 T0: 7 Rules/5 pairs. 모두 HELDOUT_CANDIDATE, 공격 검증·production 결과가 아닙니다.
T2 provider/retrieval packs와 정확 예산은 버전별 고정됐습니다. 합계 최대 174 calls, 3622912 tokens, 표준 공개가격 상한 USD 4.06이며 실제 지출이 아닙니다.
DG-XVER-PROVIDER는 USER_DECISION_REQUIRED; provider/credential/공격 접근0. DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; DG06 필수.
DEC025 제목·claim·HAI23 V2A/T0/T2·EXP03B·EXP02·EXP04/05·PILOT 결과 불변. T2>T1-B는 정상 의미 유도에 한정하며 T0보다 우수하지 않습니다.
후보 권한 META+STAT, GDN은 비인과적 learned-graph evidence, SCI02B 고정 숫자 결합, FormalV4 실행권한, guard 단방향. 37정책 재선택·META 재구성·best seed 없음.
eTaPR109 합성/가상 동등성 PASS. 다중파일/empty/secondary P1 해석은 DG05 전 결정 항목으로 유지하며 실제 eligibility는 생성하지 않았습니다. 백업 SINGLE_COPY_LOCAL_ONLY.
