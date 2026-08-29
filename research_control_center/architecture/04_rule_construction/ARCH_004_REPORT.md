# 관계와 숫자는 어떻게 Rule이 되는가

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## 1. Evidence Pack이란 무엇인가

확인된 normal delayed-response relation 하나를 rule construction에 넘기기 위한 제한된 private view다. E1은 relation마다 11개 numeric role을 보관한다. E3는 그중 horizon을 이미 고정된 relation field로 옮기고, 나머지 10개 값·reference, relation identity와 방향, 승인 evidence identity, P1/relation-family 메타데이터를 T0/T1/T1-B/T2에 전달한다.

## 2. LLM은 무엇을 받는가

LLM arm은 source/target, 두 방향, 선택된 horizon, normal-only 값과 hash reference, 승인된 evidence identity를 받는다. 값은 제한된 reasoning context로 보이지만 응답에는 값을 새로 쓰지 않고 정확한 reference만 반환해야 한다.

## 3. LLM이 받지 않는 정보

raw HAI, label, attack interval, test1 결과, utility metric, D0/D1 prediction, candidate-arm 성능, 다른 arm의 proposal·validity 결과, runtime authority를 받지 않는다. 따라서 construction 단계가 test outcome을 보고 rule을 고치는 구조는 아니다.

## 4. Rule DSL이란 무엇인가

실제 provider output은 full runtime program이 아니라 strict `ProviderProposalCoreV1` JSON이다. DSL family와 runtime-logic family가 하나로 고정되고, relation·변수·방향·horizon·numeric reference가 모두 닫힌 schema에 들어간다. project code가 provenance를 더해 proposal envelope를 만들고 task-specific validity를 적용한다. candidate core는 양 source sign과 양 target direction을 허용하지만 현재 canonical Rule v1 MVP parser의 지원 범위는 더 좁다. 따라서 canonical `DelayedResponseRuleV1` materialization과 runtime authorization은 자동으로 성립하지 않으며 ARCH-005가 그 bridge를 감사해야 한다.

## 5. LLM이 바꿀 수 있는 것 / 없는 것

모델은 같은 schema 안에서 proposal을 표현하거나 T2 follow-up에서 허용된 field를 수정할 수 있다. 하지만 새 sensor, 다른 relation, 임의 horizon, numeric literal, 새 evidence, free-form runtime code, causal claim, authority claim은 허용되지 않는다. 일부 제약은 parser/schema가 즉시 막고, semantic identity/reference mismatch는 deterministic validity가 막는다. arbitrary Python, file access, network operator는 DSL에 존재하지 않는다.

## 6. T0 Template

`run_real_t0_v1`가 frozen relation과 numeric reference를 정해진 proposal core에 직접 매핑한다. LLM call은 0이며 deterministic이다. 42개 relation 모두 task-specific validity에서 `accepted_proposal`이 되었다.

## 7. T1 One-shot

relation마다 shared initial request를 한 번 실행한다. 두 번째 scientific generation은 없다. frozen R2R cohort에서 42 call 모두 parse되고 admissible하여 42/42 relation-level accepted proposal이 되었다.

## 8. T1-B Repeat

relation마다 동일 input·prompt·model config로 stateless independent call 세 번을 모두 실행한다. 이전 proposal이나 verifier feedback은 다음 call에 보이지 않는다. 126 calls 중 125개가 parse되었고 122 proposals가 admissible했다. relation별 earliest admissible을 고르므로 41개는 call 1, 한 개는 call 3가 선택되어 42/42가 되었다.

T1-B와 T2는 최대 3-call opportunity budget과 initial condition은 공정하게 맞췄다. 그러나 T1-B는 항상 세 번, T2는 early stop이므로 실제 사용 call은 126 대 42였다. 따라서 realized cost equality라고 말할 수 없다.

## 9. T2 Verifier-feedback

T2는 최대 3 model calls, 최대 2 follow-up generations, 최대 1 same-corpus retrieval을 허용한다. parser와 `task039e0_validity_v2` 뒤 project-owned controller가 `accept`, `revise`, `retrieve`, `no_rule`을 선택한다. 모델은 orchestration을 통제하지 않고, retrieval은 새로운 과학 근거가 아니라 initial corpus의 승인 slice를 다시 보여 주는 것이다.

## 10. 실제로 Feedback이 사용됐는가

아니다. 42개 모두 첫 call에서 종료했다. 39개는 즉시 accepted였고, 3개는 unsupported-variable이라는 non-repairable validity issue로 `no_rule`이 되었다. revise 0, retrieve 0, follow-up 0, feedback recovery 0이다.

다만 구현 전체의 `no_rule` mapping은 더 넓다. response/schema failure, verifier rejection, call-budget exhaustion도 task-specific orchestrator에서 `no_rule`로 합쳐질 수 있다. 이는 generic outcome contract와 frozen protocol이 요구하는 explicit failure 분리와 맞지 않는 HIGH contract gap이다. Frozen 3건의 원인은 위의 non-repairable validity issue로 확인되지만, 이 일반 구현 gap은 별도 수정 task 전까지 남는다.

## 11. 42/42와 39/42는 정확히 무엇인가

분모는 frozen confirmed relations 42개다. 분자는 relation별 construction outcome이 `accepted_proposal`인 수다. T0 42, T1 42, T1-B 42, T2 39다. 이는 provider output 개수도, canonical Rule v1 수도, COMMON-42 membership도, runtime-authorized rule 수도, detection 성공 수도 아니다. T1-B 내부 proposal은 122개가 admissible했지만 relation-level 선택 outcome은 42개다.

## 12. 왜 현재 Agentic 효과를 주장할 수 없는가

feedback loop capability는 구현되었지만 관측 실행에서는 feedback edge가 한 번도 활성화되지 않았다. 작동하지 않은 treatment로 개선 효과를 추정할 수 없다. 현재 허용되는 표현은 “bounded verifier-feedback construction path를 구현했다”뿐이다.

## 13. Rule 생성과 탐지 성능은 왜 다른 문제인가

construction validity는 schema, relation identity, numeric reference, prohibited field와 provenance를 검사한다. rule이 test1 attack을 찾는지, false alarm이 적은지는 별도 label-aware runtime utility다. construction report 자체도 `utility_tested=false`를 기록한다.

## 14. 다음 Verifier 단계와의 연결

ARCH-005는 task-specific proposal validity와 canonical verifier, portfolio freeze, COMMON-42, runtime authorization이 실제로 어떻게 연결되는지 감사한다. 특히 `accepted_proposal`에서 `runtime authorized`로 넘어가는 authority bridge를 별도 검증해야 한다.

## ARGOS reference와 현재 구현 선택

Repository가 허용하는 구현 수준 비교만 하면, LLM-generated rule 아이디어는 typed reference-bound candidate로, numeric proposal은 normal-only numeric authority로, runtime LLM은 deterministic LLM-free execution으로, review/repair는 deterministic validity plus bounded feedback capability로 좁혀졌다. 이는 문헌 novelty나 superiority 결론이 아니다.

## 현재 결론

Construction architecture는 실제로 존재하고 frozen cohort에서 실행되었다. Evidence와 numeric authority는 LLM 밖에서 고정되며 proposal은 closed data contract다. 그러나 LLM arm은 temperature 0.7, seed 없음이므로 traceable하지만 bitwise deterministic하지 않고, T2 feedback advantage는 미검증이다.
