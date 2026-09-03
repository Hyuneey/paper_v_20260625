# EXP-04 개발 평가 결과

상태: DEVELOPMENT_ONLY · 실행 완료, 독립 결과 무결성 QA PASS.

META+STAT 기반 39-rule Formal V4 V2A portfolio가 고정된 뒤, D0·Isolation Forest·Rule-only·두 고정 confirm2 fusion의 예측을 모두 durable freeze했다. 그 후 one-shot capability로 test1 label을 해석했다. test1 결과로 수치·threshold·fusion 정책을 변경하지 않았다.

| 방법 | Attack-event Recall | Normal FAR/hour | 정상 false episode |
|---|---:|---:|---:|
| D0 PCA-SPE | 11/14 | 0.4939336325682588839451968874340932 | 7 |
| Isolation Forest | 5/14 | 1.764048687743781728375703169407476 | 25 |
| Rule-only V2A | 11/14 | 37.60951802269742644896999157176738 | 533 |
| PCA+Rule | 11/14 | 0.6350575275877614222152531409866912 | 9 |
| IF+Rule | 5/14 | 1.905172582763284266645759422960074 | 27 |

모든 5개 prediction freeze·bundle replay·post-label byte identity 검사는 PASS입니다.

## 해석

14개는 연속 공격 구간 단위(contiguous attack-event units)이며 통계적으로 독립인 14개 사건이라고 주장하지 않는다. 정상 노출은 51,019초이고 FAR/hour는 정상 false episodes × 3,600 / 51,019이다. 경계가 공격 구간과 겹치는 episode는 정상 false episode로 세지 않는다.

PCA와 Rule-only는 both 9, PCA only 2, Rule only 2, neither 1이다. Rule-only가 PCA 미탐 3개 중 2개에 반응했지만 고정 confirm2 fusion은 회수 0/3이다. IF와 Rule-only는 both 5, IF only 0, Rule only 6, neither 3이고, IF 미탐 9개 중 Rule-only 반응은 6개이나 fusion 회수는 0/9이다.

두 fusion은 각 기준 탐지기의 Recall을 유지했으나 정상 false episode를 각각 2개 추가했다. incremental Recall=0, incremental FAR/hour=0.1411238950195025382700562535525981이다. 이 동결 정책의 탐지 개선 주장은 DEVELOPMENT_NOT_SUPPORTED다. 이후 새 fusion이나 threshold를 만들지 않았다.

Isolation Forest는 더 강한 후보 baseline으로 사전 선정됐지만 관찰 결과가 PCA보다 우수하지 않았다. 이름만으로 superior detector라고 설명하지 않는다. Rule-only FAR 37.6095/hour는 여전히 높아 운영 효용은 미검증이다. V1 D1과 규칙 cohort/수치가 다르므로 FAR 차이를 통제된 개선 효과로 해석하지 않는다.

원본 V2 결과 hash: `0f3f5966a35e35ae663e60ddbb8afb7ce62e35081a7f9383e9aaf61b75064db1`. PILOT V1은 별도 frozen authority이고 이 표로 덮어쓰지 않는다. held-out 일반화는 UNCONFIRMED.
