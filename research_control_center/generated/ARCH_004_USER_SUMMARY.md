<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=c752d7a6fd77b3de559afb880cb003a45b9cd44fa9ba8113133949ddc6f347f2 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# Rule은 어떻게 만들어지는가

## Evidence Pack

정상 데이터에서 확인한 relation을 제한된 construction view로 만든다. E1의 11개 role 중
horizon은 fixed relation field로, 나머지 10개는 값과 reference로 보인다. raw HAI, label,
attack, test/utility outcome, D0/D1 result와 runtime authority는 포함되지 않는다.

## LLM과 DSL 경계

LLM은 값을 볼 수 있지만 output에는 승인 reference만 반환한다. strict proposal schema에는
arbitrary numeric literal, Python, file/network access, 새 operator, free-form runtime logic가 없다.
새 variable이나 relation/horizon mismatch는 뒤의 deterministic validity가 거부한다.

## 네 construction arm

| Arm | LLM | Call policy | Frozen relation outcome |
|---|---|---|---|
| T0 | no | local deterministic template | 42/42 accepted proposal |
| T1 | yes | one call | 42/42 accepted proposal |
| T1-B | yes | three stateless calls, earliest admissible | 42/42 selected proposal |
| T2 | yes | maximum three, bounded feedback | 39/42 accepted; 3 no_rule |

T1-B는 126 calls를 모두 썼고, T2는 42 calls 모두 call 1에서 종료했다. 따라서 maximum
opportunity budget은 비교 가능하지만 realized cost가 같다고 말할 수 없다.

## Feedback은 실제 사용됐는가?

Bounded verifier-feedback capability is implemented. The frozen cohort exercised no revise or retrieve action, so no feedback improvement was demonstrated.

T2의 세 no_rule은 unsupported-variable non-repairable validity issue였다. revise 0, retrieve 0,
follow-up 0이다. 따라서 “feedback improved quality”라고 말할 수 없다.

주의: task-specific orchestrator는 response/schema failure, verifier rejection, budget exhaustion도
`no_rule`로 합칠 수 있다. 이는 generic/frozen protocol의 explicit-failure 분리와 맞지 않는 HIGH
contract gap이며, frozen 세 건의 구체 원인을 바꾸지는 않는다.

## 42/42의 정확한 뜻

relation-level `accepted_proposal` 수다. canonical Rule v1 materialization, COMMON-42 membership,
runtime authorization 또는 detection performance 수가 아니다. `no_rule`은 construction의
fail-closed outcome이며 runtime `abstain`과 다르다.

## 재현성

T0는 frozen input에서 deterministic하다. LLM arms는 model/config, prompt, evidence, request,
response와 ledger hash가 추적되지만 temperature 0.7, seed 없음이므로 bitwise deterministic하지 않다.

다음 task는 **HAI-XVER-NORMAL-PREP-001**이다.

## 현재 DG-04 / 외부 준비 Gate

HAI-XVER-NORMAL-PREP-001: APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES.
이전 BLOCKED_GDN_METHOD_CHANGE_REQUIRED의 estimator 역할 선택은 사용자 승인으로 해소됐습니다.
Provider train1 / bounded retrieval train2에는 EXP03B-compatible split-pure GLOBAL 5-row GDN만 사용합니다.
SCI01 split-local event와 seed별 purged validation 교집합의 EVENT 10-row는 AUXILIARY_CORROBORATION_ONLY입니다.
Global/event 융합, event의 provider·retrieval·verifier·candidate 사용, train3/4 또는 numeric policy 기반 event 선택을 금지합니다.
3개 seed 전부 유지; best-seed 선택 없음. 별도 타입과 실제 frozen projector adapter 합성검사 15 PASS 및 독립 scoped QA PASS.
과학적 역할 binding은 완료됐지만 버전별 execution adapter·custody·environment·performance preflight 통합은 남아 있습니다.
현재 GDN scientific runs 0/12, 외부 T0·T2 pack·정확 token/cost 미완료; provider/credential/공격0.
DG-03B_REVISED 승인으로 완료된 EXP03B와 기존 DEC-025 / Stage A / V2A39 / T0 22 / T2 Repeat1 21 Rules / EXP02 / EXP04/05 / PILOT 결과는 불변입니다.
T2 > T1-B는 정상-only 의미 유도 비교에 한정되고 T0보다 우수하지 않습니다.
DG-03C의 현재 gate명 DG-XVER-PROVIDER는 NOT_READY_EVIDENCE_PENDING; DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; vault SINGLE_COPY_LOCAL_ONLY.
