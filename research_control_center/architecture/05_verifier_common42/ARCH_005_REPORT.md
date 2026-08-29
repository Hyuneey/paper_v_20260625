# Rule 후보는 어떻게 실제 실행 규칙이 되는가

## 1. Proposal과 Rule은 무엇이 다른가

TASK-039E proposal은 하나의 confirmed relation에 묶인 닫힌 construction 후보다. canonical `DelayedResponseRuleV1`은 graph, evidence, parameter, split, output와 authority를 포함하는 더 큰 계약이다. frozen construction path에는 proposal을 canonical Rule v1으로 lossless하게 바꾸는 bridge가 없다.

## 2. Deterministic Verifier란 무엇인가

canonical `VerifierV1`은 `DelayedResponseRuleV1`과 bound artifact collection을 20개 순서 고정 stage로 검사한다. task039e0 validity V2는 별도 모듈이며 E0 proposal을 relation/evidence/budget에 맞춰 검사한다.

## 3. 무엇을 검증하는가

Canonical verifier는 schema, 변수 type/allowlist, subsystem/graph edge, relation family, unit, lag/window, parameter 승인과 provenance, split, evidence/normal reference, conflict/duplicate, complexity, output/explanation, claim boundary를 검사한다. Task validity는 proposal field closure, relation/sign/horizon, numeric reference, arm/budget/construction provenance와 prohibited input을 검사한다.

## 4. 무엇은 검증하지 못하는가

두 verifier 모두 물리적 진실, causality, 탐지 utility, optimality, generalization을 증명하지 않는다. verifier acceptance는 scientific validation이 아니다.

## 5. Task-specific validity와 canonical verifier

관계는 `PARTIALLY_OVERLAPPING`, authority는 `NON_EQUIVALENT_BY_DESIGN`이다. 서로 공통 개념은 있지만 object와 check가 다르고, 어느 쪽의 PASS도 다른 쪽 PASS를 자동 보장하지 않는다. frozen E0/COMMON-42/D1에서 canonical VerifierV1 호출은 입증되지 않았다.

## 6. accepted가 곧 실행 가능을 뜻하지 않는 이유

Task admissible과 canonical accepted 모두 runtime authority를 부여하지 않는다. portfolio membership, exact authority replay, numeric registry, implementation identity, execution scope와 receipt/grant가 추가로 필요하다.

## 7. COMMON-42란 정확히 무엇인가

42개 confirmed normal delayed-response relation의 executable projection을 V4 `CanonicalRuleDescriptorV4`로 표현한 하나의 portfolio다. `DelayedResponseRuleV1` 42개 파일이 아니다.

## 8. T0/T1/T1-B/T2와 COMMON-42 관계

T0/T1/T1-B는 42개 모두 실행 projection이 같아 하나로 deduplicate됐다. T2는 39개가 같은 projection이고 3개가 no_rule이지만 utility authority에서 제외됐다. 그래서 T2 39/42와 COMMON-42 42는 모순이 아니다.

## 9. Portfolio Freeze

42 descriptors, 420 runtime numeric references, horizon semantics, full census plan, ordering과 authority hash가 deterministic replay로 고정된다. 대체 portfolio나 stale artifact는 거부된다.

## 10. Runtime Authorization

General canonical runtime bundle과 frozen D1 authority는 서로 다른 plane이다. Frozen D1은 V4 authority, evaluator bundle, private numeric resolver custody, committed INNER grant와 one-attempt token을 사용했다.

## 11. Numeric Authority는 어떻게 다시 결속되는가

Construction E1과 runtime registry의 420 shared values는 focused audit에서 모두 같았지만 reference/authority identity는 새로 만들어졌다. 각 V4 descriptor가 열 개 reference와 numeric descriptor hash를 묶고 horizon은 descriptor에 남긴다.

## 12. Hash는 왜 필요한가

relation cohort부터 executable equivalence, reference set, numeric descriptor, 42 rule descriptors, portfolio, V4 authority, evaluator bundle, D1 grant까지 각 경계를 hash가 묶는다. 값이 같아도 authority identity가 다르면 자동으로 같은 권한이 아니다.

## 13. no_rule은 정확히 무엇인가

Intentional `no_rule`은 construction absence다. canonical verifier에는 no_rule state가 없다. Task orchestration은 response/parser/rejection/budget failure도 no_rule로 합칠 수 있어 generic interpretation에는 HIGH risk가 있다. Frozen 세 건은 sanitized evidence상 모두 non-repairable unsupported-variable validity outcome이어서 이 cohort에서는 원인이 해석 가능하다.

## 14. 현재 D1을 무엇이라고 불러야 하는가

**COMMON-42 Verified Relational Rule-only**가 가장 정확하다. “verified”는 contract/provenance/integrity로 제한한다. “Agentic Rule-only”는 부정확하고 “LLM Rule-only”도 D1 이름으로는 오해를 만든다.

## 15. 현재 남은 위험

Canonical RuleV1/verifier/runtime-authority plane과 task-specific frozen D1 plane 사이에 검증된 materialization bridge가 없다. no_rule taxonomy는 code fix가 필요하다. Runtime trace/explanation equivalence는 ARCH-006에서 계속 확인해야 한다.
