# 검증된 관계 규칙만으로 이상을 탐지하면 어떻게 되는가

## 1. D1은 정확히 무엇인가

D1은 COMMON-42의 42개 V4 verified relational descriptor를 고정 숫자 authority로 실행한 Rule-only pilot이다. T2 Agentic arm의 직접 출력은 아니다.

## 2. D1이 평가하는 Prediction은 무엇인가

6,031개의 적용 가능한 relation opportunity마다 하나의 결과 record를 만든 `ScientificRulePredictionArtifactV1`이다. Prediction object는 label을 열기 전에 완성·검증되었지만 그 시점에 별도 파일로 영속화되지는 않았다.

## 3. Rule violation / Alarm second / Episode의 차이

788개 anomalous rule record가 630개 unique decision second로 중복 제거되고, 연속 초를 묶어 626개 total alarm episode가 된다. Label을 적용한 뒤 그중 574개가 normal false episode로 분류된다.

## 4. 13/14는 무엇을 의미하는가

14개 operational attack event 가운데 적어도 하나의 alarm episode와 겹친 event가 13개라는 뜻이다. Point recall이나 precision이 아니며 통계적 독립성을 뜻하지 않는다.

## 5. 정상 구간에서는 얼마나 많이 울렸는가

51,019 normal second에서 574개 normal false episode가 있었다. 공격 반응이 높았던 동시에 정상 오경보 부담도 매우 컸다.

## 6. FAR/hour는 무엇인가

Normal false episode 수를 normal labeled exposure hour로 나눈 값이다. D1은 40.50255787059723 episodes/hour이며 point FPR과 다르다.

## 7. D0와 D1은 어떤 사건을 각각 잡았는가

둘 다 10개, D0만 1개, D1만 3개, 둘 다 놓친 사건 0개였다. 이는 같은 사건 집합에서 두 신호가 완전히 같지 않음을 보여준다.

## 8. D1은 D0가 놓친 사건을 잡았는가

현재 pilot에서는 그렇다. D0가 놓친 3개 모두에 D1이 반응했다. 이는 **VERIFIED_PILOT_OBSERVATION**이다.

## 9. 이것을 Complementarity라고 부를 수 있는가

Pilot complementarity signal이라고는 부를 수 있다. 그러나 독립 사건 수가 작고 held-out 결과가 없으며 operational FAR가 높으므로 일반적·통계적·운영적 complementarity는 아직 검증되지 않았다.

## 10. 왜 높은 Recall만으로 좋은 Detector가 아닌가

공격 민감도와 정상 false-alarm 부담은 별도 축이다. 13/14만 보고 D1이 D0보다 우수하다고 결론내릴 수 없다.

## 11. D1을 LLM Rule-only라고 불러도 되는가

직접 LLM-arm runtime 결과라는 의미라면 안 된다. COMMON-42는 T0/T1/T1-B 공통 실행 의미를 가진 portfolio다.

## 12. D1을 Agentic Rule-only라고 불러도 되는가

안 된다. T2는 COMMON-42에서 제외되었고 현재 D1은 T2-specific runtime이 아니다.

## 13. 현재 Rule-only 결과에서 말할 수 있는 것

현재 INNER pilot에서 13/14 event response, 매우 높은 normal false-alarm burden, D0와 다른 response pattern이 있었다고 말할 수 있다.

## 14. 아직 말할 수 없는 것

Rule-only의 일반적 우월성, operational utility, validated complementarity, held-out generalization, Agentic/LLM construction advantage는 말할 수 없다.

## 15. 다음 본격 검증에서 필요한 것

더 큰 독립 사건 집합, validation/final-test 분리, durable prediction-before-label gate, stronger multivariate detector, 사전 고정된 comparison/fusion policy가 필요하다.
