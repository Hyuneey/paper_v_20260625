# Detector contiguous-buffer hash 성능 개선

상태: `IMPLEMENTED_SYNTHETIC_CONFORMANCE_PASS_NOT_YET_SCIENTIFICALLY_EXECUTED`

## 문제

Isolation Forest와 PCA-SPE V2의 matrix/score authority hash는 기존에
`array.tobytes(order="C")`를 사용했다. 큰 normal matrix에서는 이미 존재하는
contiguous NumPy buffer 전체를 별도 Python `bytes`로 복사하고, prefix가 있는 경우
결합 bytes를 한 번 더 만들 수 있다. 이는 모델 연산과 무관한 메모리 peak 및 copy
비용이다.

## 변경

`_sha256_contiguous_array_v1`은 다음만 수행한다.

1. 호출자가 준비한 C-contiguous array buffer를 `memoryview`로 연다.
2. 기존과 동일한 canonical prefix bytes를 먼저 SHA-256에 입력한다.
3. array의 C-order raw byte view를 그대로 SHA-256에 입력한다.
4. 비연속 배열과 non-bytes prefix는 fail-closed한다.

적용 위치:

- `NormalMatrixInputV1` matrix binding hash
- Isolation Forest combined fit matrix hash
- Isolation Forest calibration score hash
- PCA-SPE calibration score hash

## Byte equivalence

Synthetic 1D/2D `float64`, `0.0`, `-0.0`, 일반 실수, canonical prefix 조합에서:

`sha256(prefix + array.tobytes(order="C"))`

와 새 contiguous-buffer hash가 exact lowercase SHA-256으로 일치했다. 기존
matrix binding hash contract와 receipt field 의미는 변경되지 않았다.

## 메모리 확인

1,000,000개 `float64` synthetic array에 대한 동일-process `tracemalloc` 확인:

- digest equality: PASS
- 기존 `prefix + tobytes`: peak 16,000,082 bytes
- contiguous-buffer hash: peak 664 bytes
- 전체-array Python bytes allocation 제거: PASS

이 수치는 synthetic implementation evidence이며 scientific runtime 속도나 detector
성능 결과가 아니다.

## 최종 검증

- VALIDATION V2 suite: 304 tests OK, 6 expected skips 포함
- RCC suite: 165 tests PASS
- RCC registry/privacy: PASS, `private_exposures=0`
- changed-file privacy scan: 6 files, findings 0
- PILOT V1 preservation: 3,021/3,021 blobs PASS

Isolation Forest exact optional environment는 현재 bundled test interpreter에서
dependency closure 불일치로 기존 정책에 따라 SKIP됐다. Hash byte-equivalence는
dependency-independent synthetic test로 검증했고 PCA-SPE detector regression은
PASS했다. 전체-tree host-path scanner의 기존 synthetic private-path rejection
fixture 1건은 원격 base와 byte-identical이며 이번 변경에서 수정하지 않았다.

## 계산 자원 판단

분류는 `CPU_MEMORY_COPY_OVERHEAD`다. GPU로 옮길 연산이 아니라 CPU memory copy를
제거한 것이며 detector config의 `n_jobs=1`도 변경하지 않았다.

## 과학적 안전

- model architecture/config: 변경 0
- hyperparameter/seed/dtype/data/split/protocol: 변경 0
- threshold/comparator/metric: 변경 0
- 기존 digest/receipt semantics: 변경 0
- scientific execution: 0
- test1/test2/held-out/label access: 0
- PILOT V1 변경: 0
- scientific result 변경: 0

## 남은 병목

HAI CSV의 Python row parsing과 cross-method split 공유는 별도 session/custody
contract가 필요하다. 이번 변경은 디스크 cache나 scientific frame 재사용을
추가하지 않는다.
