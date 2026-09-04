# EXP-03 — 승인된 고정 snapshot 실행 계약

## 변경하지 않는 과학 범위

기존 preregistration, V2A 39-rule portfolio, EXP-02, EXP-04/05, detector/fusion은 불변이다.
이 실험은 새로운 규칙 발견이나 성능 평가가 아니라 **동결 관계에 대한 제한된 reference 기반
Formal V4 구성 적합성**을 비교한다. RuleV1/VerifierV1이 V4 runtime을 직접 승인한다는 주장은 하지 않는다.

39개 관계 × T0 1회 및 T1/T1-B/T2 각 3회 = 390 terminal records.
T1-B는 성공해도 3개 독립 응답을 모두 보존하고 가장 이른 admissible draw를 선택한다.
T2는 ACCEPT 즉시 종료하며 최대 3회다. 실제 사용량과 최대 budget은 따로 보고한다.

## 입력과 출력

모든 arm은 동일한 공개 관계 identity/direction/horizon 및 10개 numeric reference를 받는다.
summary hash는 기존 normal confirmation의 identity metadata를 명시적으로 새 버전에 결속한다.
통계적 support 값을 새로 계산하거나 숨은 수치를 추론하지 않는다.
private numeric authority는 hash/role/reference를 로컬에서만 재생하며 provider에는 보내지 않는다.

새 출력 envelope는 `RULE` 또는 `NO_RULE`이다. RULE의 모든 source/target/direction/horizon/reference는
실제 응답에서 검사한다. 오류 필드를 기대값으로 덮어써서 ACCEPT하지 않는다.
검사 통과 시 실제 응답 필드로 기존 FormalV4RuleDescriptorV1을 구성하고 descriptor hash를 비교한다.
이는 비교용 executable projection이며 portfolio/runtime의 변경이나 재배포가 아니다.

relation identity/source/target/direction/horizon 불일치는 기존 action map대로 nonrepairable이다.
numeric reference 불일치만 같은 corpus의 reference를 1회 retrieve하고 이후 revise할 수 있다.
parse failure, refusal, incomplete output은 별도 terminal이며 no_rule로 바꾸지 않는다.
NO_RULE 적합성은 기존 validator의 **구조적 계약 확인**이지 expert 판단이나 실제 근거 부족의 증명이 아니다.

## API 및 비용

- snapshot: `gpt-5.4-mini-2026-03-17`; alias/fallback 금지
- endpoint: `https://api.openai.com/v1/responses`
- reasoning: `none`; temperature: `0.7`; top_p: `1.0`; seed 미전송
- strict JSON schema; stateless; store=false; tools=[]; service_tier=default
- scientific concurrency=1; 자동 retry=0; timeout=60초
- 최대 819 calls / input 3,354,624 / output 1,677,312 / total 5,031,936
- call당 4,096/2,048; standard-API 상한 USD 10.07
- 단가 $0.75/M input + $4.50/M output; cached discount를 상한에 반영하지 않는다.

전체 serialized 요청 UTF-8 byte 수 + 512 server-framing reserve를 보수적 **추정 상한**으로 쓴다.
이는 server tokenizer와 동등성 증명이 아니다. 실제 usage도 매 응답 검증하며 초과/누락은 즉시 중단한다.
첫 과학 호출은 정규 schedule의 첫 T1 slot이다. 모델/usage/schema/영속 receipt PASS 뒤에만
나머지를 실행한다. ACCEPT 자체를 첫 호출 gate 조건으로 삼아 결과를 선별하지 않는다.

## 영속 통제

단일 writer lock → append-only 예약 → fsync/close/replay → 단발 dispatch permit → HTTP 1회
→ private response bytes 보존 → usage/model 재생 → 비용 정산 → verifier/controller → terminal freeze.
호출/출력/비용/latency는 하나의 hash-chain ledger에 event 종류별로 보존한다.
모든 승인/입력/schema/code hash를 동결한다. ledger prefix 삭제/rollback은 sequence/tip 검사로 거절한다.
불확실한 전송은 최대 4,096/2,048 token 책임을 예약 상태로 남기고 재전송 없이 중단한다.
중단/부분 schedule은 성공 denominator로 줄여 보고하지 않는다.

## synthetic stress와 해석

natural과 synthetic stress는 분리한다. stress는 39 × 10 사전 지정 terminal/controller fixture이며
provider 호출은 0이다. natural feedback이 없으면 Agentic benefit은 미입증이다.
관계·반복·arm별 terminal/call/비용과 repeat stability를 보고하고, 빈 repair denominator는 NOT_OBSERVED다.
추가 provider, test1 재접근, 신규 attack/held-out 접근은 없다. 완료 후 DG-04에서 멈춘다.

공식 모델/가격: https://developers.openai.com/api/docs/models/gpt-5.4-mini
