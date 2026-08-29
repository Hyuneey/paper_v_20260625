# 우리가 보고 있는 성능 숫자는 정확히 어떻게 만들어지는가

## 1. 먼저 구분해야 할 단위

D0의 SPE score와 point alarm, D1의 opportunity·rule record·alarm second, D2의 combined Boolean alarm은 서로 다른 원시 출력이다. 공통 metric은 이를 alarm second로 정규화한 뒤 episode, attack-event unit, Recall, FAR/hour 순서로 올린다. 숫자는 단계가 다르면 직접 비교할 수 없다.

## 2. Point Alarm이란 무엇인가

test1의 한 physical row에서 alarm이 참인 상태다. D0와 D2는 54,000행 Boolean prediction을 직접 가진다. D1은 `evaluated_anomaly` rule record의 `decision_physical_row_index`만 alarm row로 내보낸다.

## 3. Alarm Episode란 무엇인가

alarm row를 set으로 중복 제거하고 정렬한 뒤, 바로 다음 row(`+1`)만 같은 episode로 합친 maximal contiguous run이다. 허용 gap은 0행이고 interval은 `[start,end)`다. D0 876 point alarms는 46 episodes가 되고, D1 788 anomalous rule records는 630 unique alarm seconds와 626 episodes가 된다.

## 4. Attack-event Unit은 어떻게 만드는가

정렬된 test1 label에서 strict `1`이 연속되는 최대 구간을 하나의 unit으로 만든다. label은 `timestamp,label` 54,000행 계약이며 0/1 이외 token은 허용하지 않는다. ARCH-010은 private label payload를 열지 않고 기존 manifest와 integrity evidence만 감사했다.

## 5. 14개의 의미

test1에는 이 정책으로 고정된 14개 contiguous attack-event units가 있다. 이는 operational grouping이며 통계적 독립성은 분석되지 않았다. 따라서 “14 independent attacks”라고 쓰면 안 된다.

## 6. Attack-event Recall은 어떻게 계산하는가

한 alarm episode가 attack unit과 한 row라도 half-open overlap하면 그 unit은 detected다. grace window, 최소 지속시간, label dilation, point adjustment는 없다. Recall은 `detected units / 14`다. Frozen 결과는 D0 11/14, D1 13/14, D2 V1 11/14, D2 V2 11/14다.

## 7. 정상 False Episode는 무엇인가

어떤 attack unit과도 겹치지 않는 alarm episode다. attack과 일부라도 겹치는 mixed episode는 나누지 않고 normal false numerator에서 제외한다. 단순히 boundary를 맞닿는 것은 half-open overlap이 아니다.

## 8. FAR/hour는 어떻게 계산하는가

strict label `0` row가 51,019초의 normal exposure를 만든다. `normal false episodes / (51,019 / 3600)`이 FAR/hour다. 이는 point-level FPR이 아니다. Frozen 값은 D0 7 episodes / 0.4939336325682589, D1 574 / 40.50255787059723, V1 10 / 0.7056194750975128, V2 98 / 6.915070855955625다.

## 9. D0는 어떤 형태로 metric에 들어가는가

Durably persisted and replayed label-blind Boolean prediction에서 true row를 alarm second로 가져온다. 이후 공통 episode/event semantics를 적용한다.

## 10. D1은 어떤 형태로 metric에 들어가는가

6,031 opportunities 가운데 terminal anomaly record만 사용한다. 같은 decision row의 여러 rule violations는 하나의 alarm second로 중복 제거된다. non-opportunity, non-alarm, abstain은 common Boolean interface에서 alarm timestamp를 만들지 않는다. Frozen D1 abstain은 0이지만, runtime 의미와 metric의 `NO_ALARM` 표현은 구분해야 한다.

## 11. D2는 어떤 형태로 metric에 들어가는가

V1/V2는 D0 alarm을 보존하고 정책이 허용한 D1 evidence를 더한 완전한 per-second Boolean prediction이다. 두 prediction은 label 전에 durable persistence/replay되었다. V2는 test1-informed development이므로 독립 confirmation이 아니다.

## 12. 세 방법을 같은 Recall/FAR로 비교해도 되는가

분류는 `SEMANTICALLY_EQUIVALENT`와 `FAIR_WITH_LIMITATIONS`다. 같은 test1, event units, exposure, overlap, grouping, Recall/FAR 공식을 쓴다. 다만 D0/D2는 매 row를 평가하고 D1은 opportunity가 있을 때만 판단한다. 구현 wrapper도 완전히 동일하지 않다.

## 13. D0 / D1 overlap은 어떻게 계산했는가

각 방법의 14-unit detection vector를 비교했다. BOTH 10, D0_ONLY 1, D1_ONLY 3, NEITHER 0이다. 따라서 D1은 pilot에서 D0 miss 3/3에 반응했지만 V1/V2 recovery는 각각 0/3이다. 이는 secondary diagnostic이지 일반 complementarity 증명이 아니다.

## 14. Result Integrity Audit은 무엇을 보장하는가

예상 prediction/label identity, row count와 ordering, metric arithmetic, result/report binding, mutation/replay 기록을 점검한다. D0와 D2에는 durable file-before-label gate가 있다. D1은 label 전에 완전한 object를 validate하고 shallow-freeze했지만 durable file gate는 없었다.

## 15. 무엇은 보장하지 못하는가

Integrity PASS는 sample size, event independence, test1 재사용 문제, generalization, superiority, operational utility를 보장하지 않는다. D1 downstream audit도 이전 durable gate 부재를 대신할 수 없다. 권위 있는 frozen inferential statistics는 없다.

## 16. 현재 pilot 결과 표

| Method | Attack-event Recall | Normal FAR/hour | Alarm episodes | Status |
|---|---:|---:|---:|---|
| D0 | 11/14 | 0.4939336325682589 | 46 | INNER PILOT |
| D1 | 13/14 | 40.50255787059723 | 626 | INNER PILOT |
| D2 V1 | 11/14 | 0.7056194750975128 | 49 | FROZEN PILOT POLICY |
| D2 V2 | 11/14 | 6.915070855955625 | 143 | TEST1_INFORMED_DEVELOPMENT |

## 17. 현재 말할 수 있는 것 / 없는 것

Frozen metric arithmetic과 artifact lineage는 감사됐다. D1은 현재 pilot에서 D0와 다른 event-unit response를 보였고 descriptive Recall이 높았지만 normal FAR 부담도 매우 컸다. 현재 V1/V2는 D0 Recall을 늘리지 못했다. 그러나 14 units의 독립성, 일반 complementarity, 방법 우수성, held-out generalization은 모두 미확인이다.

다음 단계는 실험 재실행이 아니라 **GAP-000 — Pre-Validation Remediation & Risk Triage**다. GAP-000 이후에만 ARCH-011을 검토한다.
