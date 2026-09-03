<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=7843bc595fd526de37fa6765d7982848c00d23c6391d954f25e1ba155557c3ea authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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
다음: DG-03 provider 예산·승인 검토. DG-04 제목, DG-05 held-out, DG-06 실제 제출은 별도 Gate입니다.


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
  **할 일:** EXP-03 natural cohort와 정확한 provider/model·call/token 상한을 먼저 확정하고 DG-03 실행 승인을 검토한다.
  **사용자 확인이 필요한 이유:** 현재 provider 호출은 0이며 기호적 예산만으로 호출을 승인할 수 없다.
  **연결 문서:** research_control_center/validation_v2/DECISION_GATES.md
  **상태:** 미결정

- **ID:** USER-V2-004
  **우선순위:** 높음 (HIGH)
  **할 일:** DG-04에서 GDN-Assisted 제목과 조건부 Agentic 표현을 결정한다.
  **사용자 확인이 필요한 이유:** EXP-01/01B 음성 결과를 유지하며 EXP-01C는 LEARNED_GRAPH_SUPPORTING이다.
  **연결 문서:** DEC-021
  **상태:** 미결정
## 필수 향후 Gate

- **ID:** USER-V2-005
  **우선순위:** 높음 (HIGH)
  **할 일:** test2/heldout 접근 전에 새 held-out 연구의 사전등록과 DG-05 승인을 검토한다.
  **사용자 확인이 필요한 이유:** 이미 소진된 기존 OUTER protocol을 재시도하지 않는다.
  **연결 문서:** DG-05
  **상태:** 미결정
## 검토 필요

- **ID:** USER-V2-006
  **우선순위:** 높음 (HIGH)
  **할 일:** 실제 EXP04/05 결과가 포함된 교수님 package를 제출 전에 검토한다.
  **사용자 확인이 필요한 이유:** DG-06 전 이메일을 보내지 않는다.
  **연결 문서:** docs/professor_experiment_update_v2/01_ONE_PAGE_SUMMARY.md
  **상태:** 미결정

과학 source authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
