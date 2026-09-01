# Formal V4 prepared runtime 효율화

상태: `IMPLEMENTED_SYNTHETIC_CONFORMANCE_PASS_NOT_YET_SCIENTIFICALLY_EXECUTED`

## 문제

기존 `execute_formal_v4_rule_v1`은 한 opportunity를 평가할 때마다 execution
context, portfolio, relation authority, numeric authority와 파일 결속을 전부 다시
검증한다. 단건 감사 API로는 강한 fail-closed 경계지만, 수천 opportunity의 D1 또는
EXP-05 실행에서는 같은 JSON read/hash/replay가 반복되는 CPU·I/O 병목이 된다.

## 구현

VALIDATION V2 전용으로 다음 별도 경로를 추가했다.

1. `prepare_formal_v4_runtime_session_v1`
   - 전체 runtime authorization과 실제 bound bytes를 먼저 재생 검증한다.
   - start authority replay 뒤 lookup cache 구성용 numeric authority JSON을 한 번
     읽어 모든 descriptor의 정확한 numeric binding을 확인한다.
   - relation ID → descriptor/parameter immutable lookup을 준비한다.
2. `execute_prepared_formal_v4_rule_v1`
   - window마다 파일을 다시 읽지 않는다.
   - 기존 단건 runtime과 같은 numeric domain 검증 및 판정 함수를 사용한다.
   - relation, feature/file/sampling contract, horizon 좌표를 계속 fail-closed로 검사한다.
3. `finalize_formal_v4_runtime_session_v1`
   - session을 먼저 비활성화한다.
   - execution context와 모든 bound artifact를 다시 hash/replay한다.
   - 시작 이후 한 byte라도 바뀌면 receipt 없이 실패하고 session 재사용도 거부한다.

Scientific runner의 기본 진입점은 `execute_formal_v4_batch_v1`이다. 이 함수는 전체
window trace를 메모리에 보류하고 종료 authority replay가 PASS한 뒤에만 trace와
finalization receipt를 함께 반환한다. Low-level prepared trace는 finalization 전까지
provisional이며 결과 artifact로 공개하거나 metric에 넘겨서는 안 된다.

기존 `execute_formal_v4_rule_v1`은 유지된다. 즉, 단건 감사용 매 호출 full replay와
대량 실행용 start/end replay가 명확히 분리됐다.

## 합성 conformance

- PASS: bit-identical trace
- FAIL: bit-identical trace
- source ABSTAIN: bit-identical trace
- incomplete target ABSTAIN: bit-identical trace
- 다른 horizon/direction relation: bit-identical trace
- numeric lookup-cache document batch load: 1회
- 준비 후 25 window bound-file read: 0회
- 종료 authority replay: PASS
- 종료 전 bound numeric byte mutation: 검출 및 session 영구 비활성화
- forged/finalized session: 실행 거부

이 결과는 합성 conformance이며 D1 성능 결과가 아니다. V2 portfolio가 생성된 뒤
scientific runner가 이 경로를 사용하도록 연결하기 전에는 실제 scientific execution
상태를 올리지 않는다.

## 계산 자원 판단

이 병목은 작은 rule 산술이 아니라 반복 파일 hash/JSON parse와 Python lookup이므로
`CPU/IO_BOUND`다. GPU 사용은 부적절하다. 이번 변경은 model, rule semantics,
hyperparameter, seed, split, numeric authority 또는 metric을 변경하지 않는다.

## 안전

- PILOT V1 변경: 0
- scientific execution: 0
- test1/test2/held-out/label access: 0
- provider call: 0
- raw/private value 공개: 0
