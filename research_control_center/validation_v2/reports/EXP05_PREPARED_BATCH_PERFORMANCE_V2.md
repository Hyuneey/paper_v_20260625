# EXP-05 prepared batch 성능 개선

상태: `IMPLEMENTED_SYNTHETIC_CONFORMANCE_PASS_NOT_YET_SCIENTIFICALLY_EXECUTED`

## 목적

기존 `execute_and_materialize_formal_v4_rule_v1`은 한 unit마다 Formal V4
authority와 numeric authority를 다시 읽고 검증한다. EXP-05 cohort가 커지면 동일한
결속 파일을 opportunity 수만큼 반복 읽는 CPU/IO 병목이 된다.

이번 개선은 이미 검증된 prepared Formal V4 runtime을 EXP-05에 연결한다.

1. EXP-05 run authorization을 한 번 검증한다.
2. batch 시작 시 Formal V4 authority 전체를 replay한다.
3. descriptor와 numeric parameter를 불변 lookup으로 준비한다.
4. 각 window를 정확히 한 번 실행한다.
5. batch 종료 시 bound artifact 전체를 다시 replay한다.
6. 종료 replay가 PASS한 뒤에만 trace를 materialize·render·fidelity validate한다.
7. ordered unit hash와 runtime finalization receipt를 하나의 batch hash로 결속한다.

## 보존된 의미

- 기존 single-unit API와 산출 unit byte/document 의미를 변경하지 않았다.
- 각 unit의 trace, explanation, fidelity result, materialization receipt는 direct
  경로와 bit-identical이다.
- 기존 unit별 durable freeze와 cohort custody 형식을 변경하지 않았다.
- prepared batch는 custody를 생략하지 않는다. 반환된 unit은 기존 EXP-05 durable
  persistence 경로에 그대로 전달되어야 한다.
- authority가 batch 도중 바뀌면 종료 replay가 실패하고 batch를 반환하지 않는다.
- precomputed trace를 받는 공개 API는 추가하지 않았다.

## 성능 경계

Synthetic conformance에서 batch 크기를 2개에서 20개로 늘려도 bound-file
`Path.read_bytes` 횟수는 증가하지 않았다. 8개 window 비교에서는 기존 direct
경로보다 prepared batch의 bound-file read 수가 작았다. 이는 scientific runtime
시간이나 성능 결과가 아니라 반복 authority replay 제거에 대한 구조적 증거다.

## 검증

- direct vs prepared EXP-05 unit: bit-identical PASS
- runtime window execution count: window당 정확히 1회 PASS
- start/end authority replay: PASS
- mid-batch authority mutation: fail-closed PASS
- empty/list batch, unit substitution, forged finalization receipt: rejection PASS
- batch schema/registry replay: PASS
- 기존 EXP-05 custody regression: PASS

최종 회귀 결과:

- VALIDATION V2 suite: 299 tests OK, 6 expected skips 포함
- RCC suite: 162 tests PASS
- RCC registry/privacy: PASS, `private_exposures=0`
- changed-file privacy scan: 9 files, findings 0
- PILOT V1 preservation: 3,021/3,021 blobs PASS

전체-tree host-path scanner는 이 변경과 무관하게 기존
`tests/test_validation_v2_prediction_custody_v1.py`의 synthetic private-path
거절 fixture 1건을 차단 대상으로 보고한다. 해당 파일은 원격 base와 byte-identical이며
이번 작업에서 scanner를 약화시키거나 fixture를 변경하지 않았다.

## 계산 자원 판단

분류는 `CPU_IO_BOUND`이다. 병목은 neural-network tensor 연산이 아니라 JSON/file
authority replay이므로 GPU 사용은 부적절하다.

## 과학적 안전

- scientific execution: 0
- test1/test2/held-out/label access: 0
- provider/LLM call: 0
- architecture/hyperparameter/seed/data/protocol 변경: 0
- PILOT V1 변경: 0
- scientific result 변경: 0

## 남은 경계

이 경로의 실제 `SCIENTIFIC_V2` 사용은 V2 portfolio, EXP-05 cohort, scientific
authorization이 동결된 뒤에만 허용된다. 이번 작업은 synthetic conformance와
성능 contract 구현이며 EXP-05 과학 결과를 생성하지 않았다.
