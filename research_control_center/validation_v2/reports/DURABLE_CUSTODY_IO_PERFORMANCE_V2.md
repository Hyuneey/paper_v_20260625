# VALIDATION V2 durable prediction/evaluation custody I/O 성능 개선

상태: `IMPLEMENTED_SYNTHETIC_CONFORMANCE_QA_PASS_NOT_SCIENTIFICALLY_EXECUTED`

## 대상

- `prediction_custody_v1`: D1 prediction-before-label freeze와 label-access lease
- `evaluation_custody_v1`: dense method prediction, exact-method bundle, 공통 evaluation
  label-access lease

두 경로 모두 VALIDATION V2 전용이며 PILOT V1 custody나 frozen artifact를 수정하지
않는다.

## 확인된 중복

기존 no-overwrite publish는 임시파일을 fsync·close한 뒤 임시파일 전체를 읽고,
hard-link 게시 후 최종 파일을 다시 읽었다. 일부 상위 함수는 이미 reopen된 bytes를
검증한 직후 동일 최종 파일을 다시 읽어 receipt binding 또는 반환 artifact를 만들었다.
evaluation label authorization은 replay 때 읽은 prediction·receipt·bundle bytes를
capability binding hash 계산을 위해 다시 읽었다.

## 변경

1. temporary write, file `fsync`, close, hard-link no-overwrite publish, temporary unlink,
   directory `fsync`를 유지한다.
2. 게시된 최종 파일을 한 번 reopen하고 입력 bytes와 비교한다.
3. 그 reopened bytes를 JSON/schema/hash/receipt binding에 재사용한다.
4. evaluation replay 결과는 private immutable carrier로 path, parsed artifact, receipt,
   검증된 byte digest를 전달한다. raw JSON bytes를 method 수만큼 보유하지 않는다.
5. label capability binding은 authorization 단계에서 이미 완전 replay된 digest를
   재사용한다.
6. label read 직전, label reader 종료 직후, post-metric 단계의 실제 파일 재검증은
   전혀 줄이지 않았다.

## 구조적 전체-file read 결과

| 경로 | 변경 전 | 변경 후 | 감소 |
|---|---:|---:|---:|
| D1 prediction persist | 5 | 2 | 60.0% |
| D1 standalone replay | 2 | 2 | 변경 없음 |
| D1 label authorization | 4 | 3 | 25.0% |
| dense prediction persist | 5 | 2 | 60.0% |
| dense prediction standalone replay | 3 | 2 | 33.3% |
| 2-method evaluation bundle freeze | 9 | 6 | 33.3% |
| 2-method evaluation label authorization | 15 | 7 | 53.3% |

일반적인 `M`개 method authorization의 핵심 read 수는 `4M + 7`에서 `2M + 3`으로
감소한다. 이 수치는 wall-clock benchmark가 아니라 코드 경로에서 계측한
deterministic full-file reopen 횟수다.

## 유지된 과학·governance 의미

- prediction-before-label durable boundary 유지
- exact-method bundle freeze 유지
- label-access-before-freeze rejection 유지
- opaque one-shot capability 유지
- duplicate authorization rejection 유지
- prediction/receipt/bundle/lease mutation fail-closed 유지
- label reader 실패 시 capability 소비 유지
- concurrent consume/authorize 단일 성공 유지
- output document, schema, hash, receipt field 변경 0

## 검증

- focused custody suites: 47 tests PASS, 2 expected skips 포함
- VALIDATION V2 suite: 316 tests PASS, 6 expected skips 포함
- persist/replay/authorize file-read count regression: PASS
- overwrite/partial/symlink/junction/hard-link failure regression: PASS
- pre/post-label mutation and one-shot regression: PASS
- replay 완료 후 capability 등록 사이 mutation rejection: PASS

## 계산 자원 판단

분류는 `IO_BOUND`다. GPU를 사용할 작업이 아니며, scientific configuration을
바꾸지 않고 중복 file reopen과 재hash만 제거했다.

## 안전

- scientific execution: 0
- test1/test2/held-out/label access: 0
- architecture/hyperparameter/seed/data/protocol 변경: 0
- PILOT V1 변경: 0
- frozen result 변경: 0
