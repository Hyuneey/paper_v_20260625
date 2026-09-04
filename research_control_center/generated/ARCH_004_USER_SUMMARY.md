<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=0679baf23b38ac292c9ec0334debce0277b7bbb1b7d17558ff90374c40286fe3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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

다음 task는 **DG-XVER-PROVIDER**이다.

## 현재 DG-04 / 외부 준비 Gate

HAI-XVER-NORMAL-PREP-001: 정상-only 실행 완료, 독립 최종 QA PASS. DG-XVER-PROVIDER에서 정지합니다.
HAI22/HAI21 GDN은 각각6회, 총12회입니다. GLOBAL5는 train1 provider / train2 retrieval, EVENT10은 보조 분석 전용이며 융합·후보·verifier·T0·숫자·guard 사용을 금지합니다.
HAI22 T0: 13 Rules/12 pairs. HAI21 T0: 7 Rules/5 pairs. 모두 HELDOUT_CANDIDATE, 공격 검증·production 결과가 아닙니다.
T2 provider/retrieval packs와 정확 예산은 버전별 고정됐습니다. 합계 최대 174 calls, 3622912 tokens, 표준 공개가격 상한 USD 4.06이며 실제 지출이 아닙니다.
DG-XVER-PROVIDER는 USER_DECISION_REQUIRED; provider/credential/공격 접근0. DG05 NOT_APPROVED; 교수 package NOT_SUBMITTED; DG06 필수.
DEC025 제목·claim·HAI23 V2A/T0/T2·EXP03B·EXP02·EXP04/05·PILOT 결과 불변. T2>T1-B는 정상 의미 유도에 한정하며 T0보다 우수하지 않습니다.
후보 권한 META+STAT, GDN은 비인과적 learned-graph evidence, SCI02B 고정 숫자 결합, FormalV4 실행권한, guard 단방향. 37정책 재선택·META 재구성·best seed 없음.
eTaPR109 합성/가상 동등성 PASS. 다중파일/empty/secondary P1 해석은 DG05 전 결정 항목으로 유지하며 실제 eligibility는 생성하지 않았습니다. 백업 SINGLE_COPY_LOCAL_ONLY.
