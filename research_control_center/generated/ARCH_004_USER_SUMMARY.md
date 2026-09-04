<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=ff5895a48395a92c97930f1c6b72d5583c95b0df7eb675bbe21b768d168a8b6a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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

다음 task는 **DG-04 후속 정상 준비 — BLOCKED_NORMAL_DATA_CUSTODY (schema-only projection 범위 확인)**이다.

## 현재 DG-04 / 외부 준비 Gate

DG-04 / DEC-025 승인 완료. DG-03B_REVISED 승인 후 동결한 EXP-03B에서 T2는 T1-B 대비 이점이 있으나 T0보다 우수하지 않았습니다. T0 22 Rules, T2 Repeat 1 21 Rules는 별도 HELDOUT_CANDIDATE이며 V2A39·기존 결과는 불변입니다.

Stage B는 BLOCKED_NORMAL_DATA_CUSTODY. 공식 정상 train1 두 컨테이너의 byte identity 검증 후 embedded label schema에서 중단했습니다. label 값 해석·과학 사용 0이며 정상 컨테이너 byte traversal은 있었습니다. 추가 header 접근 자동심사를 우회하지 않았습니다. Schema-only label 식별 및 feature-only projection 범위를 확인해야 합니다.

외부 STAT/GDN/T0 미실행, DG-03C N/token/cost 미정. eTaPR109 synthetic per-file 일치; 버전 내 집계는 미정. Provider·credential·공격 payload 0. 상세: validation_v2/dg04_xver_prep/CURRENT_PREPARATION_STATUS_V1.md. 전체 task PASS가 아니며 integration merge/push·교수 제출은 하지 않습니다.
