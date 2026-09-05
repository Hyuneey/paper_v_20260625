<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=188187c9dc94da7b8e9354af38d8db038c2b9c449b89744fa677e321844c038b authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 결정이 필요한 사항

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
다음: DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access. DG-03 provider 승인, DG-04 제목, DG-05 attack panel, DG-06 실제 제출은 서로 별도 Gate입니다.


## DG-04 — EXP-03B 이후 최종 기여 결정

USER_DECISION_REQUIRED. DG-03B_REVISED 승인 실행·독립 QA 완료. 판정 `AGENTIC_ADVANTAGE_SUPPORTED`. 518 calls; provider의 numeric policy 선택 없음. [결과·한계·다음 결정](validation_v2/exp03b/execution_v2/EXP03B_RESULTS_REPORT_V1.md).

EXP-03 V1 및 V2A·EXP04/05 보존. 추가 Agentic rescue 금지. DG-05 공격 접근·DG-06 실제 제출은 별도 승인입니다.

과학 source authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 현재 승인된 DG-04 및 실제 중단 지점

MULTIPANEL-PRE-DG05-FREEZE-001 COMPLETE_QA_PASS. HAI22/21 PCA-SPE and secondary Isolation Forest are frozen from label-blind normal projections. Five primary methods per panel, immutable Fusion, method-blind P1 eligibility, official-scenario metrics, file-namespaced eTaPR, empty-input behavior, paired contrasts, and the global prediction-before-any-label custody state machine are frozen. No attack/test/label/scenario data was accessed. Current phase PRE_DG05_FROZEN; exact next DG-05 USER_DECISION_REQUIRED. Professor package NOT_SUBMITTED; backup SINGLE_COPY_LOCAL_ONLY.
