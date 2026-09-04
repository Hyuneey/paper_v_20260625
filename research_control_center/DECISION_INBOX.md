<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=073cac6b59ccb55f5028c6eaef8d8d9e952e42d6df500ceaf1f780e24212e814 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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
다음: HAI-XVER-NORMAL-PREP-001. DG-03 provider 승인, DG-04 제목, DG-05 attack panel, DG-06 실제 제출은 서로 별도 Gate입니다.


## DG-04 — EXP-03B 이후 최종 기여 결정

USER_DECISION_REQUIRED. DG-03B_REVISED 승인 실행·독립 QA 완료. 판정 `AGENTIC_ADVANTAGE_SUPPORTED`. 518 calls; provider의 numeric policy 선택 없음. [결과·한계·다음 결정](validation_v2/exp03b/execution_v2/EXP03B_RESULTS_REPORT_V1.md).

EXP-03 V1 및 V2A·EXP04/05 보존. 추가 Agentic rescue 금지. DG-05 공격 접근·DG-06 실제 제출은 별도 승인입니다.

과학 source authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 현재 승인된 DG-04 및 실제 중단 지점

DG-04 / DEC-025와 Stage A는 불변입니다. DG-03B_REVISED 승인 후 동결된 EXP-03B에서 T2는 matched-budget T1-B 대비 이점이 있지만 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules, V2A39는 별도 authority입니다.

사용자 schema-only allowlist projection 승인으로 정상 custody 차단을 해결했습니다. HAI22 train1~6/HAI21 train1~3 모두 NORMAL_ONLY_CUSTODY_READY. Label 이름은 header metadata로만 관찰하고 값 decode·검증·사용0. META/STAT union은 각29pairs, GDN admission0입니다.

현재 BLOCKED_PENDING_HAI_XVER_NORMAL_PREP: external GDN context/evidence, T0, provider packs 미완료. DG-XVER-PROVIDER exact token/cost 미정, calls0. eTaPR per-file109 PASS; 세 metric binding은 공격 전 결정 필요. 공격·credential0, 제출/merge/push 없음.
