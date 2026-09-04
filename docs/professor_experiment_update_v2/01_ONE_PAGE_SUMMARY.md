# 교수님 실험 업데이트 — VALIDATION V2

EXP-01·EXP-01B 및 EXP-02 정상 데이터 실행을 완료한 뒤, V2A 39-rule portfolio로 EXP-04 개발 평가와 실제 EXP-05 trace 전체 생성을 마쳤습니다. PILOT V1 source/artifact/result는 그대로 보존했습니다.

| 방법 | Attack-event Recall | Normal FAR/hour | 정상 false episode |
|---|---:|---:|---:|
| D0 PCA-SPE | 11/14 | 0.4939336325682588839451968874340932 | 7 |
| Isolation Forest | 5/14 | 1.764048687743781728375703169407476 | 25 |
| Rule-only V2A | 11/14 | 37.60951802269742644896999157176738 | 533 |
| PCA+Rule | 11/14 | 0.6350575275877614222152531409866912 | 9 |
| IF+Rule | 5/14 | 1.905172582763284266645759422960074 | 27 |

핵심 결과: 두 fixed fusion은 Recall 개선 없이 FAR가 증가했습니다. Rule-only의 높은 FAR 문제는 남아 있습니다. Isolation Forest도 이 test1에서는 PCA보다 우수하지 않았습니다. 음성 결과를 유지하며 결과 후 정책 변경은 하지 않았습니다.

## 교수님 피드백에 따른 GDN Prediction Model + XAI 추가 검증

과거 EXP-01/01B ablation 결과는 그대로이고 EXP-01C의 결과는 LEARNED_GRAPH_SUPPORTING입니다. 안정적 양성 pair 2개는 V2A의 일부 동일 horizon과 연결됐습니다. GDN은 설명용 sidecar이고 META+STAT 후보 권한이나 Formal V4 탐지 결과를 바꾸지 않습니다. 잠정 GDN-Assisted 표현은 DG-04에서 검토합니다.

## 검증 수준

test1은 DEVELOPMENT_ONLY입니다. 14개 contiguous attack-event units의 독립성과 held-out 일반화는 미확인입니다. EXP-05 실제 trace는 6,418개이며 human usefulness는 평가하지 않았습니다. 새 환경의 기존 PASS는 synthetic rehearsal일 뿐 이번 과학 결과를 fresh-machine에서 재생한 것은 아닙니다.

test1·공격 label·test2·held-out 접근을 구분합니다: test1 features는 승인된 예측 단계에서, label은 모든 5개 예측 동결 후에만 해석했습니다. test2/held-out 접근은 0입니다. EXP-04/05 당시 provider 호출은 0이었고, 이후 별도 DG-03 승인 EXP-03에서 585회 호출했습니다. EXP-03은 test1을 다시 열지 않았습니다.

DG-03 승인 아래 EXP-03 실행·QA가 완료됐으며 다음은 DG-04 기여 표현 결정입니다. Agentic 이점은 아직 지원되지 않으며 EXP-06 runtime LLM은 불필요합니다. 이 package는 작성본이며 DG-06 전 실제 제출하지 않습니다.
