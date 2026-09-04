<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=e46d8693784d1b02603c10764c3a14f9a8ee34266d00953472cfa581a1c90937 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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
다음: DG-03B_REVISED — EXP-03B Provider Execution Decision (DG-04 DEFERRED_UNTIL_EXP03B). DG-03 provider 승인, DG-04 제목, DG-05 attack panel, DG-06 실제 제출은 서로 별도 Gate입니다.


## DG-03B_REVISED — EXP-03B 의미적 추론 provider 승인 필요

USER_DECISION_REQUIRED. 최대609회 / 8,463,360 tokens / USD11.03. 고정 snapshot gpt-5.4-mini-2026-03-17. Provider numeric option은 제거했고 SCI02B에서 후결속합니다. 현재 호출0이며 이전 승인·예산은 상속하지 않습니다.

[정확한 예산·privacy brief](validation_v2/exp03b/DG03B_PROVIDER_DECISION_BRIEF_V2.md)

DEC-024 Amendment2 과학 단순화는 승인 완료지만 이 별도 provider 예산은 미승인입니다. DG-04는 EXP03B 이후입니다.

과학 source authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
