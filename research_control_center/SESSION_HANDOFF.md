# EXP03B-PAYLOAD-REDUCE-001 — 현재 준비 상태

상태 PREPARED_DG03B_REVISED_PENDING. EXP-03B는 RULE_SET/NO_RULE·source/target direction·horizon만 추론합니다. numeric option은 provider에서 제거했고 모든 출력·train2 admission·train3 평가가 frozen된 뒤 고정 EXP02 policy를 SCI02B로 결속합니다. 기존 SCI01/04와 disposition 기준은 유지합니다.
29 pair, 20 structural rows(+5 GDN horizon rows/STAT), numeric rows740→0. 고정 gpt-5.4-mini-2026-03-17; 최대 609 calls, input 7,216,128, output 1,247,232, total 8,463,360, USD 11.03. 기존80,373,993 input/USD65.90은 historical superseded이며 새 승인으로 사용하지 않습니다.
DG-03B_REVISED 별도 승인 전 provider/credential/probe0. DG-04는 EXP03B 이후입니다. EXP03V1·V2A39·EXP04/05·PILOT 불변; test1/2/heldout/외부공격 접근 없음. Private vault는 SINGLE_COPY_LOCAL_ONLY. 최신 지침: validation_v2/exp03b/EXP03B_PROVIDER_EXECUTION_INSTRUCTION_V2.md.

## 이전 기록 — 역사적 보존·현재 승인값 아님

# 현재 세션 인계 — EXP03B-BIND-001

SCI-01~04 승인 사항을 구현하고 train1 provider/T0 및 train2 hidden evidence 29 pair를 준비했습니다. train3는 frozen reference만 재생했으며 train4는 guard 입력 identity만 확인했습니다. 실제 provider/guard 결과는 없습니다.
상태 PREPARED_DG03B_PENDING. 다음은 DG-03B 신규 승인입니다. model gpt-5.4-mini-2026-03-17, 609 calls, input 80373993, output 1247232, 총 81621225, USD 65.90.
기존 audit7c의 SCI 미정 blocker는 사용자 승인으로 해소됐습니다. EXP03 V1은 CONSTRAINED_RULE_MATERIALIZATION_BENCHMARK로 보존. DG-04는 EXP03B 이후로 연기. test1/2/외부공격/provider 접근 금지 유지.
private vault는 SINGLE_COPY_LOCAL_ONLY이며 독립 backup을 주장하지 않습니다. 지침: validation_v2/exp03b/EXP03B_PROVIDER_EXECUTION_INSTRUCTION_V1.md.

## 이전 기록 — 역사적 보존

# 세션 인계 — EXP03B 준비 감사 / 과학 binding 결정 필요

## 최신 task-local 보정 (EXP03B-PREP-001)

EXP-03 V1은 `CONSTRAINED_RULE_MATERIALIZATION_BENCHMARK`로 해석하며 결과 bytes는 보존한다.
사용자가 DG-04를 EXP03B 뒤로 연기했다. 이전 DG-04 문서는 historical이며 수정하지 않는다.
EXP03B는 아직 PREPARED가 아니다: train1 T0/train2 verifier 임계값·numeric-option 선택,
normal guard admission/집계와 majority scoring의 정확한 과학 binding이 필요하다.
기존 train1 통계는 pooled train1/train2 scale에 의존하고 GDN functional evidence는 train4여서
단순 재사용할 수 없다. 실제 데이터·provider·credential 접근 없이 감사를 마쳤다.
다음: `validation_v2/exp03b/EXP03B_CONSTRUCT_VALIDITY_RATIONALE_V1.md`의 SCI-01~04 결정.
이후 나머지 준비를 완료하고 DG-03B로 간다. 현재 Registry/Dashboard는 이전 완료 상태이며
이번 미완료 task를 READY로 게시하지 않았다. 아래는 EXP-03 완료 시점의 역사적 인계다.

## 정확한 다음 작업

DG-04 — 최종 제목·Agentic 기여 표현 결정.
DG-03은 사용자 승인 exact snapshot `gpt-5.4-mini-2026-03-17`으로 완료했다.
실제 585 calls, 636,270 tokens, 표준요금 상한 USD 1.21379625; 독립 QA PASS.
T0 39/39, T1 104/117, T1-B 115/117, T2 105/117 승인. T2 feedback 0/117이므로 repair는 NOT_OBSERVED다.
41개 call-level PARSE_FAILURE는 valid JSON의 NO_RULE envelope 일관성 실패이며 기존 분류를 변경하지 않았다.
전체 응답·ledger는 별도 EXP-03 private vault namespace에 local-only로 보관됐다. 재호출·재실행하지 않는다.
공개 결과와 QA: `validation_v2/exp03/execution_v1/`. frozen result hash `653ee0d36255e22fcc0a145b9872418aeceac4022c32df71b803db3afe357238`.
DG-04 제목·기여, DG-05 다중 attack panel, DG-06 실제 교수님 제출은 별도 Gate다.

## 사용자 승인 평가 확대

- `PANEL-D`: HAI 23.05 test1 14-unit 결과는 immutable DEVELOPMENT_ONLY.
- `PANEL-H`: HAI 23.05 test2 38 nominal scenarios, future PRIMARY_HELDOUT.
- `PANEL-X1`: HAI 22.04 58 nominal scenarios, external replication 1.
- `PANEL-X2`: HAI 21.03 50 nominal scenarios, external replication 2.
- 146 nominal non-development scenarios는 IID가 아니며 primary pooled Recall을 만들지 않는다.
- 실제 P1 denominator는 outcome-blind eligibility custodian이 prediction freeze 뒤 공개한다.
- HAI22/21 P1 tag·unit·role crosswalk는 아직 `UNRESOLVED`; attack data 전에 별도 normal-only/public metadata task가 필요하다.
- HAIEnd는 HAI23과 같은 experiment에서 동시 수집된 확장 표현이므로 별도 attack panel이 아니다.

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
