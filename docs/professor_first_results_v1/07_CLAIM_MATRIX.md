# 논문 주장 매트릭스

| 주장 | 상태 | 권고 논문 문구 |
|---|---|---|
| graph-guided candidate curation | 지원 | “세 개의 분리된 후보 발견 경로를 공통 144-pair universe와 top-20 예산 안에서 통합하였다.” |
| executable verified rules | 지원 | “확인된 관계를 immutable binding과 deterministic verifier를 거친 실행 규칙으로 변환하였다.” |
| normal-only numeric authority | 지원 | “규칙 수치는 attack label이 아니라 정상 학습 데이터에서 유도된 참조 authority에 결합하였다.” |
| deterministic verifier | 지원 | “구조·evidence·parameter·split·runtime 조건을 결정론적으로 검증하였다.” |
| LLM-free runtime | 지원 | “배포 시점의 규칙 평가는 LLM 없이 결정론적으로 수행된다.” |
| INNER attack-event rule sensitivity | 지원·INNER 한정 | “COMMON-42 rule-only arm은 INNER 14개 이벤트 중 13개를 탐지했다.” |
| INNER detector–rule complementarity | 지원·INNER 한정 | “D1은 D0가 놓친 3개 이벤트를 모두 포착했고 event union은 14/14였다.” |
| reproducible negative fusion evidence | 지원 | “사전 고정된 V1/V2 결합은 D0 미탐을 회복하지 못했으며 무결성 감사로 재현됐다.” |
| combined method improves detector | 지원 안 됨 | “현재 두 결합 정책에서는 D0 대비 recall 개선이 관찰되지 않았다.” |
| rule-only operational deployment | 지원 안 됨 | “높은 정상 FAR로 인해 rule-only arm의 운용 가능성은 지지되지 않는다.” |
| D2 V1/V2 superiority | 지원 안 됨 | “V1/V2 모두 D0 recall을 넘지 못했고 V2의 FAR 비용이 더 컸다.” |
| TSFM benefit | 미확인 | “TSFM 비교는 본 연구에서 수행하지 않았으며 향후 연구다.” |
| ARTIST segment-selection benefit | 미확인 | “ARTIST식 세그먼트 선택은 구현·평가하지 않았다.” |
| agentic repair optimizes performance | 지원 안 됨 | “T2의 verifier-feedback이 성능 최적화를 이뤘다는 근거는 없다.” |
| held-out generalization | 미확인 | “test2 scientific result가 없어 외부 일반화는 평가되지 않았다.” |
| causal root-cause explanation | 지원 안 됨 | “trace는 시간적 관계 위반 근거를 제공하지만 인과 root cause를 증명하지 않는다.” |
| human explanation usefulness | 미확인 | “설명 인터페이스는 구현됐지만 사람 대상 유용성 평가는 수행하지 않았다.” |

## 논문 제목/기여의 안전한 중심

권고 중심 문구: **“Graph-guided construction and deterministic verification of executable temporal rules for explainable multivariate anomaly detection.”**

피해야 할 문구: “rules improve detector accuracy”, “causal localization”, “generalizes to held-out attacks”.

