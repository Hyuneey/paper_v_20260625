# 세션 인계 — VALIDATION V2 개발 결과 완료

## 정확한 다음 작업

DG-03 — EXP-03 Provider Execution Decision.
Provider/model·natural cohort·정확한 call/token 상한을 고정하고 사용자 승인을 받기 전 호출하지 않는다.
DG-04 제목·기여, DG-05 held-out, DG-06 실제 교수님 제출은 별도 Gate다.

## 완료된 실행 — 재실행 금지

V2-GDN-FRONT-EXP04-001은 pushed clean Commit B `94ae44dac900cce75ed83ee2801be38750afed4a`에서 실행했다.
5개 prediction과 동일 coordinate bundle을 durable freeze/replay한 뒤에만 opaque one-shot test1 label capability를 소비했다.
test1은 DEVELOPMENT_ONLY이며 통계적으로 독립이라는 근거가 없는 14 contiguous attack-event units다.
추가 tuning, 새 fusion, test2/heldout/provider/GDN training은 0.

- PCA: 11/14; FAR 0.4939336325682588839451968874340932
- Isolation Forest: 5/14; FAR 1.764048687743781728375703169407476
- Rule-only V2A: 11/14; FAR 37.60951802269742644896999157176738
- PCA+Rule: 11/14; FAR 0.6350575275877614222152531409866912
- IF+Rule: 5/14; FAR 1.905172582763284266645759422960074

두 fusion 모두 실제 미탐 회수 0, 정상 false episode +2. 음성 결과를 그대로 유지한다.
EXP-05는 6,418개 actual trace 전체, 11개 구조 검사와 replay PASS. GDN 문구 130개; human usefulness 미검증.

## 권한과 역사 보존

DEC-020 APPROVED_FORMAL_V4 / DG-01 RESOLVED_BY_USER.
Formal V4는 runtime authority이며 RuleV1/VerifierV1 직접 실행 권한이나 lossless bridge를 주장하지 않는다.
META = HYBRID_REVIEWED_METADATA: 공식 process graph + AI-assisted reviewed semantic 선언.
주 후보는 META+STAT; 29pair→21confirmed pair→39directional rule 및 EXP02 selected policy 유지.
EXP-01·EXP-01B 음성 결과는 변경하지 않음.
EXP-01C = LEARNED_GRAPH_SUPPORTING, 2pair의 pair/horizon 보조 근거만 설명 sidecar로 사용.
GDN-Assisted title eligibility STRONG은 문서 기준이며 최종 제목은 DG-04.
PILOT V1 `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` 3,021개 보존 entry 불변.

## 로컬 보존

TASK_PRIVATE_VAULT에 122개 task-scoped artifact hash/restore 기록.
SINGLE_COPY_LOCAL_ONLY: 독립 두 번째 backup이나 fresh-machine scientific reproduction을 주장하지 않는다.
이전 META reviewed input·old checkpoint locator 등 비필수 과거 artifact는 비차단 재현성 부채.
DATA-POLICY-001: HAI 23.05는 CODE_MATERIALIZED_OFFICIAL_DISTRIBUTION으로 복원하며 사용자 경로 요구가 기본이 아니다.
역사 BLOCKED_NORMAL_DATA_NOT_FOUND의 원인은 HAI_CODE_MATERIALIZATION_POLICY_NOT_PROPAGATED_TO_V2_RECOVERY_LOGIC.

## 결과 근거

- research_control_center/validation_v2/gdn_front_exp04_001/results/EXP04_RESULTS_V1.json
- research_control_center/validation_v2/gdn_front_exp04_001/results/EXP05_FULL_CENSUS_V1.json
- research_control_center/validation_v2/gdn_front_exp04_001/reports/INDEPENDENT_QA_V1.json
- docs/professor_experiment_update_v2/ (초안; 미제출)

기존 fresh-machine PASS는 과거 synthetic baseline에 한정된다.
현재 scientific code/config는 feature access 후 변경하지 않았다. 후속 변경은 새로운 사전등록/버전에서만 가능하다.
