<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=e18dcc333c9374f6afd37d3c7c1b5bcce27b7a516e16befbd28c6894526100c1 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# D1 검증된 관계 규칙 단독 평가를 쉽게 이해하기

## 1. D1은 정확히 무엇인가?

D1은 COMMON-42의 42개 verified relational descriptor를 V4 고정 runtime으로 실행한
Rule-only 방식이다. 직접 T2 Agentic arm이나 특정 LLM arm의 runtime 결과가 아니다.

## 2. 788, 630, 626은 왜 다른가?

| 숫자 | 뜻 |
|---:|---|
| 6,031 | Rule을 실제로 평가할 수 있었던 relation opportunity |
| 788 | anomaly로 끝난 rule-opportunity record |
| 630 | 여러 Rule의 같은 시점 경보를 합친 unique alarm second |
| 626 | 연속 alarm second를 묶은 total alarm episode |
| 574 | 626 episode 중 attack timestamp와 겹치지 않은 normal false episode |

## 3. 13/14는 무슨 뜻인가?

Test1의 14개 연속 label-one attack event 중 13개가 적어도 하나의 D1 alarm episode와
직접 겹쳤다는 attack-event Recall이다. Point recall이나 precision이 아니다.

## 4. 40.5 FAR/hour는 무슨 뜻인가?

51,019 normal labeled second에서 나온 574 normal false episode를 normal exposure hour로
나눈 값이 `40.50255787059723`이다. Point false-positive rate가 아니다.

## 5. 공격은 많이 잡으면서 오경보도 많은 이유는?

현재 증거가 보장하는 것은 **그 두 현상이 동시에 관찰되었다**는 사실뿐이다. Frozen report에는
high FAR의 일반적 원인 분석이 없으므로 trigger, tolerance, duplication 중 하나를 원인으로 단정하면
안 된다. 상태는 `CAUSE_NOT_YET_ANALYZED`다.

## 6. D1은 D0보다 좋은가?

그렇게 결론내릴 수 없다. D1은 event response가 13/14로 D0의 11/14보다 높았지만, normal FAR은
40.50255787059723으로 D0의 0.4939336325682589보다 훨씬 높았다. 민감도와 false-alarm burden은
별도 축이다.

## 7. D1은 D0와 다른 정보를 보는가?

현재 pilot response는 다르다. 둘 다 10개, D0만 1개, D1만 3개, 둘 다 놓친 사건 0개였다.
이는 response diversity를 보여주지만 원인이나 일반화는 증명하지 않는다.

## 8. D1이 D0가 놓친 3개 사건에 반응했다는 의미는?

현재 14-event INNER pilot에서만 확인된 중요한 signal이다. Allowed wording은 “D1이 D0 miss 3개
모두에 반응했다”이다. “Rule이 일반적으로 detector miss를 복구한다”는 아직 금지된 표현이다.

## 9. Complementarity가 입증됐는가?

아니다. Pilot complementarity signal은 있지만 statistical/general complementarity와 operational
utility는 **UNVALIDATED**다. D2 fusion policy와 결과 lineage는 ARCH-009에서 별도로 감사됐다.

## 10. D1은 LLM Rule-only 또는 Agentic Rule-only인가?

직접 LLM-arm runtime은 `NOT_DIRECTLY_TESTED`다. T2는 COMMON-42에서 제외되므로 Agentic Rule-only는
`MISLEADING_NOT_APPLICABLE`이다. 현재 이름은 **COMMON-42 Verified Relational Rule-only**이다.

## 11. Prediction은 label보다 먼저 정해졌는가?

완전한 label-blind prediction object가 label open 전에 검증되었다. 그러나 그 시점에 atomic file로
durably persisted되지는 않았다. 현재 pilot에서 verified leakage는 없지만 future validation에는 더 강한
durable gate가 필요하다.

## 12. 앞으로 무엇을 검증해야 하는가?

더 큰 독립 사건 집합, validation/final-test 분리, durable pre-label persistence, stronger detector,
사전 고정된 comparison/fusion policy가 필요하다.

기억할 한 문장: **D1은 D0와 다른 pilot event response를 보였지만 normal false-alarm 부담이 매우 높아,
Rule-only utility와 complementarity는 아직 검증되지 않았다.**

다음 task는 **ARCH-010 — Metrics / Episode Construction / Result Integrity Deep Audit**이다.
