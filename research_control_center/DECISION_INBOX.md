<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=ff5895a48395a92c97930f1c6b72d5583c95b0df7eb675bbe21b768d168a8b6a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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
다음: DG-04 후속 정상 준비 — BLOCKED_NORMAL_DATA_CUSTODY (schema-only projection 범위 확인). DG-03 provider 승인, DG-04 제목, DG-05 attack panel, DG-06 실제 제출은 서로 별도 Gate입니다.


## DG-04 — EXP-03B 이후 최종 기여 결정

USER_DECISION_REQUIRED. DG-03B_REVISED 승인 실행·독립 QA 완료. 판정 `AGENTIC_ADVANTAGE_SUPPORTED`. 518 calls; provider의 numeric policy 선택 없음. [결과·한계·다음 결정](validation_v2/exp03b/execution_v2/EXP03B_RESULTS_REPORT_V1.md).

EXP-03 V1 및 V2A·EXP04/05 보존. 추가 Agentic rescue 금지. DG-05 공격 접근·DG-06 실제 제출은 별도 승인입니다.

과학 source authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 현재 승인된 DG-04 및 실제 중단 지점

DG-04 / DEC-025 승인 완료. DG-03B_REVISED 승인 후 동결한 EXP-03B에서 T2는 T1-B 대비 이점이 있으나 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules는 별도 HELDOUT_CANDIDATE이며 V2A39·기존 결과는 불변입니다.

Stage B는 BLOCKED_NORMAL_DATA_CUSTODY. 공식 정상 train1 두 컨테이너의 byte identity 검증 후 embedded label schema에서 중단했습니다. label 값 해석·과학 사용 0이며 정상 컨테이너 byte traversal은 있었습니다. 추가 header 접근 자동심사를 우회하지 않았습니다. Schema-only label 식별 및 feature-only projection 범위를 확인해야 합니다.

외부 STAT/GDN/T0 미실행, DG-03C N/token/cost 미정. eTaPR109 synthetic per-file 일치; 버전 내 집계는 미정. Provider·credential·공격 payload 0. 상세: validation_v2/dg04_xver_prep/CURRENT_PREPARATION_STATUS_V1.md. 전체 task PASS가 아니며 integration merge/push·교수 제출은 하지 않습니다.
