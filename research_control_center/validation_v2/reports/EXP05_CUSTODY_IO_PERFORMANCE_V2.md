# EXP-05 durable custody I/O 성능 개선

상태: `IMPLEMENTED_SYNTHETIC_CONFORMANCE_QA_PASS_NOT_SCIENTIFICALLY_EXECUTED`

## 확인된 병목

기존 EXP-05 persistence는 full unit 또는 cohort bundle의 artifact와 receipt를 각각
다음 순서로 읽었다.

1. fsync·close된 임시파일을 다시 읽어 입력 bytes와 비교
2. no-overwrite hard-link 게시 후 최종 파일을 다시 읽어 입력 bytes와 비교
3. persistence 함수가 공개 replay 함수를 호출해 같은 최종 파일을 다시 읽고
   JSON/schema/hash/typed binding을 검증

따라서 한 저장 작업은 artifact 3회와 receipt 3회, 총 6회의 전체-file reopen을
수행했다. 이 중 임시파일과 직후 공개 replay의 추가 읽기는 최종 게시 파일의
reopen bytes를 재사용하면 제거할 수 있다.

## 변경

- atomic temporary write, file `fsync`, close, no-overwrite hard-link publish,
  temporary unlink, directory `fsync` 경계를 그대로 유지했다.
- 게시된 최종 artifact와 receipt를 각각 정확히 한 번 reopen한다.
- 그 reopened bytes를 byte-equality 확인과 JSON/schema/hash/typed replay에 함께 쓴다.
- 독립적인 공개 replay API는 artifact와 receipt를 각각 한 번 읽는 기존 기능을
  유지한다.
- bundle의 `bundle_file_sha256`은 같은 canonical bytes를 다시 직렬화하지 않고
  이미 생성된 bytes에서 직접 계산한다. digest 의미와 값은 동일하다.

## 구조적 I/O 결과

| 경로 | 변경 전 전체-file read | 변경 후 전체-file read | 감소 |
|---|---:|---:|---:|
| full evaluated unit persist | 6 | 2 | 66.7% |
| cohort bundle persist | 6 | 2 | 66.7% |
| standalone replay | 2 | 2 | 변경 없음 |

합성 regression은 `Path.read_bytes`를 계측해 persist마다 artifact와 receipt가
정확히 한 번씩만 읽히는 것을 강제한다. output schema, canonical document,
receipt hash, mutation rejection, partial-write rejection, overwrite rejection은
기존 테스트와 동일하게 PASS했다.

## 계산 자원 판단

분류는 `IO_BOUND`다. JSON 파일의 durable publication/replay 경로이므로 GPU는
적합하지 않다. 작은 cohort에서는 절대 시간 차이가 작을 수 있으나, unit 수가
증가해도 불필요한 전체-file read가 누적되지 않도록 구조적으로 제한했다.

## 과학적 안전

- durability/custody state 변경: 0
- schema/artifact/receipt field 변경: 0
- scientific architecture/hyperparameter/seed/data/protocol 변경: 0
- scientific execution: 0
- test1/test2/held-out/label access: 0
- PILOT V1 변경: 0
- scientific result 변경: 0

## 검증

- EXP-05 custody 전용: 10 tests PASS
- VALIDATION V2 전체: 313 tests PASS, 6 expected skips 포함
- single-reopen structural regression: PASS
- mutation/partial-write/no-overwrite regression: PASS

