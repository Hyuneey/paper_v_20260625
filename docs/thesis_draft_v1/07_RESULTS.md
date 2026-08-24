# 6. 결과

## 6.1 주 결과

| Arm | detected attack events | Attack-event Recall | normal false-alarm episodes | Normal FAR/hour | D0 miss recovery |
|---|---:|---:|---:|---:|---:|
| D0 PCA-SPE | 11/14 | 0.7857142857142857 | 7 | 0.4939336325682589 | baseline |
| D1 COMMON-42 | 13/14 | 0.9285714285714286 | 574 | 40.50255787059723 | 3/3 |
| D2 V1 | 11/14 | 0.7857142857142857 | 10 | 0.7056194750975128 | 0/3 |
| D2 V2 | 11/14 | 0.7857142857142857 | 98 | 6.915070855955625 | 0/3 |

14개 attack event만 있으므로 D1을 D0보다 통계적으로 우월하다고 부르지
않는다. D1의 높은 recall은 매우 높은 normal FAR와 함께 해석해야 한다.

## 6.2 Event-level complementarity

| Event set | count |
|---|---:|
| D0_AND_D1 | 10 |
| D0_ONLY | 1 |
| D1_ONLY | 3 |
| neither | 0 |
| union | 14/14 |

D0는 11/14, D1은 13/14를 탐지했다. D0가 놓친 3개 event는 모두 D1_ONLY에
포함된다. 따라서 rule layer가 reference detector와 다른 event evidence를
포함한다는 RQ3의 INNER 근거가 있다. 그러나 D1의 FAR는 40.50255787059723
episodes/hour이므로 rule-only deployability는 지지되지 않는다.

## 6.3 D2 V1 실패 분석

D2 V1은 D0 alarm을 보존하고, 동일 physical second에 적어도 두 개의
distinct source에서 D1 alarm이 있을 때만 recovery alarm을 추가했다. D0
miss이면서 D1이 탐지한 세 event의 frozen diagnostic은 다음 구조를 보였다.

- 한 event는 single-source evidence만 포함했다.
- 두 event는 multi-source evidence를 포함했지만 source signal이 서로 다른
  시점에 나타났다.

따라서 세 event 모두 exact same-second 2-source gate를 충족하지 못했다.
V1은 D0 miss를 0/3만 회복했고 incremental recall은 0.0이었다. normal FAR는
D0 대비 증가해 0.7056194750975128이 됐다.

## 6.4 D2 V2 실패 분석

V2는 asynchronous evidence 손실을 줄이기 위해 각 rule의 native horizon
동안 evidence token을 유지했다. token은 rule decision index에서 시작해
`decision index + native horizon`까지 causal/inclusive하게 활성화된다.
같은 source의 duplicate는 한 번만 세고 두 distinct source를 요구한다.

이 변화는 corroboration과 normal rule-recovery episode를 크게 늘렸다.
그럼에도 D0 miss recovery는 0/3이고 incremental recall은 0.0이었다. V2의
normal false-alarm episode는 98개, Normal FAR는 6.915070855955625였다.
normal V2 rule-recovery false-alarm episode는 92개였고 Added Normal
Rule-Recovery FAR는 6.4916991708971175였다. D0 대비 incremental normal
false-alarm episode는 91개, Incremental Normal FAR는 6.421137223387365였다.

즉 temporal memory는 signal availability를 늘렸지만 useful recovery를
만들지 못했고 false-alarm burden을 확대했다.

## 6.5 결과의 중앙 해석

`RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED`

event-level complementarity는 point-level fusion gate의 성공을 보장하지
않는다. union 14/14는 사후적으로 두 prediction set을 합친 coverage이며,
label-blind 운영 정책이 그 event를 정확히 선택할 수 있다는 뜻이 아니다.
V1은 시간 구조를 버렸고, V2는 시간 구조를 보존했지만 정상 evidence도
함께 확대했다. RQ4에 대한 현재 답은 두 단순 deterministic fusion이
incremental utility를 만들지 못했다는 것이다.

## 6.6 대표 설명 사례

아래 예는 공개 COMMON-42 descriptor의 sanitized 관계다. 수치 threshold와
attack coordinate는 포함하지 않는다.

| 사례 | source → target | expected temporal relation | satisfaction trace 요약 | 설명하는 것 / 증명하지 않는 것 |
|---|---|---|---|---|
| A | 유량 제어 command/feedback `P1_FCV01D` → 유량 sensor `P1_FT02` | step-up 후 1초 내 target decrease | source stability → step-up → 1초 response check → direction mismatch 시 violation | 밸브 전이와 유량 반응의 위반 위치 / 고장 원인 아님 |
| B | 압력 제어 valve `P1_PCV01D` → pressure sensor `P1_PIT01` | step-up 후 60초 내 target increase | transition → native 60초 window → expected increase → outcome | 느린 압력 관계와 시간 창 / 공격 주체 아님 |
| C | 수위 제어 valve `P1_LCV01D` → pressure sensor `P1_PIT01` | step-up 후 10초 내 target decrease | stability/trigger → 10초 response → evidence-bound outcome | 교차 변수 관계의 시간 localization / causal root cause 아님 |

이 interface는 transition–variable pair–horizon–expected response–outcome을
제공한다. ARTIST식 learned segment selection이나 human usefulness 평가를
대체했다고 주장하지 않는다.

## 6.7 Held-out evaluation status

사전등록된 held-out 평가는 data-custody boundary에서 test2 feature bytes나
labels를 읽기 전에 중단되어 과학 결과를 만들지 못했다.

| 항목 | 기록 |
|---|---:|
| feature custody access attempt | 1 |
| feature byte reads | 0 |
| feature semantic parses | 0 |
| label accesses | 0 |
| OUTER D0/D1/D2 executions | 0/0/0 |
| predictions | none |
| metrics | none |

따라서 OUTER는 negative scientific result가 아니며 generalization은
unconfirmed다.
