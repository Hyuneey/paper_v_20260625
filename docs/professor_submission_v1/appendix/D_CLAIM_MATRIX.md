# 부록 D — 주장 경계

## 지원되는 주장

| 주장 | 권고 문구 |
|---|---|
| graph-guided candidate curation | 공통 후보 범위 안에서 metadata, statistics, graph ranking을 결합해 관계 후보를 선별했다. |
| executable verified rules | 확인된 시간 관계를 deterministic verifier를 거친 실행 규칙으로 변환했다. |
| normal-only numeric control | 규칙 수치는 attack label이 아니라 정상 학습 데이터에서 결정했다. |
| LLM-free runtime | 최종 규칙 평가는 LLM 없이 결정론적으로 수행된다. |
| INNER rule sensitivity | 42-rule arm은 INNER 14개 이벤트 중 13개를 탐지했다. |
| event-level complementarity | 규칙은 기준 탐지기가 놓친 3개 이벤트를 모두 포착했다. |
| negative fusion evidence | 사전 고정된 두 fusion은 D0 미탐을 회복하지 못했다. |

## 지원되지 않거나 아직 확인되지 않은 주장

| 주장 | 안전한 문구 |
|---|---|
| combined method improves detector | 현재 두 fusion에서는 D0 대비 recall 개선이 관찰되지 않았다. |
| rule-only operational deployment | 높은 정상 FAR 때문에 운용 가능성은 지지되지 않는다. |
| D2 V1/V2 superiority | 두 정책 모두 D0 recall을 넘지 못했고 V2 FAR이 더 컸다. |
| TSFM benefit | TSFM은 구현·평가하지 않았다. |
| ARTIST benefit | ARTIST식 segment selection은 구현·평가하지 않았다. |
| agentic repair optimization | verifier-feedback이 성능을 높였다는 근거는 없다. |
| held-out generalization | held-out 과학 결과가 없어 일반화는 확인되지 않았다. |
| causal root-cause explanation | trace는 시간 관계 위반을 보여주지만 인과 원인을 증명하지 않는다. |
| human explanation usefulness | 설명 인터페이스는 구현했지만 사람 대상 평가는 하지 않았다. |

## 잠정 기여 문장

**PROVISIONAL_PENDING_PROFESSOR_APPROVAL**

> Graph-guided construction and deterministic verification of executable
> temporal rules for explainable multivariate anomaly detection, with an
> INNER evaluation of detector–rule complementarity and transparent negative
> evidence from two preregistered fusion policies.
