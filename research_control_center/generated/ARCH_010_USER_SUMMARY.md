<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=9e16b8482351007c7c7a47539230833ee5dd6560378b6076c1b19590c09d011a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# 성능 숫자를 어떻게 읽어야 하는가

## 1. alarm point와 episode는 무엇이 다른가?

Point는 한 physical row의 alarm이다. Episode는 중복을 없앤 alarm row 가운데 정확히 1행씩
이어지는 최대 구간이다. D0의 876 points가 46 episodes가 되는 이유다.

## 2. D1 rule record와 alarm second는 무엇이 다른가?

같은 second에 여러 rule이 깨질 수 있다. Frozen D1의 788 anomalous records는 row 중복을 없애면
630 alarm seconds이고, 이를 연속 구간으로 묶으면 626 episodes다.

## 3. attack-event unit은 무엇인가?

Strict label `1`이 연속되는 최대 구간이다. test1에는 14 contiguous units가 있다.

## 4. 왜 14개를 독립 사건이라고 하면 안 되는가?

연속 label grouping은 operational unit만 만든다. unit 사이의 통계적 독립성 분석은 없었다.

## 5. 11/14와 13/14는 어떻게 계산되는가?

Alarm episode가 attack unit과 한 row라도 겹치면 그 unit은 detected다. D0는 11개, D1은 13개를
detected했다. Point recall이나 precision이 아니다. Grace window나 point adjustment도 없다.

## 6. FAR/hour는 무엇인가?

Attack unit과 전혀 겹치지 않는 normal false episodes를 51,019 normal seconds의 시간으로 나눈
episodes/hour다. D0 0.4939336325682589, D1 40.50255787059723, V1 0.7056194750975128,
V2 6.915070855955625다.

## 7. 왜 point FPR과 다른가?

분자는 false point 수가 아니라 grouped episode 수다. 분모도 normal point 비율이 아니라 exposure hours다.

## 8. D0/D1/D2를 같은 metric으로 비교할 수 있는가?

같은 test1, event units, exposure, overlap, episode grouping, Recall/FAR 공식을 사용하므로 common
interface 비교는 가능하다. 다만 D0/D2는 모든 row를 평가하고 D1은 opportunity-driven이므로
`FAIR_WITH_LIMITATIONS`다.

## 9. D1 abstain/non-opportunity는 metric에서 어떻게 처리되는가?

Alarm timestamp를 만들지 않아 Boolean interface에서는 `NO_ALARM`처럼 작동한다. Runtime의
ABSTAIN/NO_OPPORTUNITY 의미 자체가 정상 판정으로 바뀌었다는 뜻은 아니다. Frozen abstain은 0이다.

## 10. result integrity audit은 무엇을 보장하는가?

Prediction/label identity, ordering, row closure, arithmetic, mutation/replay, report binding을 보장한다.
D0/D2는 durable pre-label file gate가 있고 D1은 더 약한 in-memory object gate다.

## 11. 왜 integrity PASS가 성능 검증 PASS가 아닌가?

Integrity는 sample size, event independence, development-set reuse, generalization, superiority, utility를
검사하지 않는다. V2도 여전히 test1-informed development다.

## 12. 현재 pilot 결과에서 무엇까지 믿어도 되는가?

고정 artifact에 기록된 현재 pilot의 descriptive Recall/FAR와 D0/D1 response diversity까지다. 일반
complementarity, held-out generalization, 통계적 우수성은 미확인이다.

기억할 한 문장: **결과 무결성은 숫자가 고정 artifact와 맞는지 보장하지만, 그 숫자가 일반 성능을
증명하는지는 보장하지 않는다.**

ARCH-011은 완료되었다. 다음 관리 task는 **MULTIPANEL-PRE-DG05-FREEZE-001**이다.

## 현재 DG-04 / 외부 준비 Gate

XVER-T2-PROVIDER-EXEC-001: COMPLETE_NORMAL_ONLY / QA PASS.
정확한 snapshot gpt-5.4-mini-2026-03-17로 HAI22 61회, HAI21 61회, 합계 122회 호출했습니다. retry/fallback/tools/4차 호출은 0이며 EVENT10은 전송하지 않았습니다.
실제 계량 사용량은 입력 333954 / 출력 13563 / 합계 347517 tokens이고 표준 공개가격 단순 산식은 USD 0.311499입니다. 이는 청구서가 아닙니다.
HAI22 T2는 train2 입장 20 pairs, 정상 확인 31 Rules, Formal V4 31, train4 유지 19 Rules/16 pairs입니다.
HAI21 T2는 train2 입장 18 pairs, 정상 확인 9 Rules, Formal V4 9, Block B 유지 2 Rules/1 pairs입니다.
두 결과는 HELDOUT_CANDIDATE이며 공격 검증·production·T2>T0 일반화 결론이 아닙니다. T0/T2/V2A는 별도 사전등록 방법으로 유지하며 선택하지 않았습니다.
모든 provider 출력과 admission을 양 버전에서 먼저 닫은 뒤 train3/Block A, SCI02B, Formal V4, 단방향 guard를 수행했습니다. 공격/test/label/real eligibility 접근은 0입니다.
DG-XVER-PROVIDER는 승인·실행 완료. DG05는 NOT_APPROVED, 교수 package는 NOT_SUBMITTED, DG06 필수입니다.
정확한 다음 작업은 MULTIPANEL-PRE-DG05-FREEZE-001이며 multi-file aggregation, empty-input, secondary P1 해석과 최종 prediction-before-label custody를 공격 접근 전에 고정합니다. 백업은 SINGLE_COPY_LOCAL_ONLY입니다.
