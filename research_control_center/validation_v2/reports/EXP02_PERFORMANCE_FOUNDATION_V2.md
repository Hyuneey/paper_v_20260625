# EXP-02 실행 효율화 기반

상태: `IMPLEMENTED_SYNTHETIC_ONLY_SCIENTIFIC_BINDINGS_STILL_REQUIRED`

## 구현 결과

EXP-02의 동결된 과학적 선택 의미를 바꾸지 않고, 장시간 반복 계산을 예방하는
실행 기반을 `paperworks.validation_v2.exp02_runner_v1`에 추가했다.

- `train1`과 `train2`는 후보 반복문 밖에서 각각 한 번만 연다.
- 두 fit split의 relation summary producer는 한 번의 batch callback으로 호출한다.
- 정확한 37개 후보(공통 1개 + 관계별 36개)를 먼저 닫고 고정한다.
- `train4`는 후보 고정 receipt가 검증된 뒤에만 한 번 연다.
- 후보 평가기는 37개 후보 전체를 한 번의 batch callback으로 받는다.
- 결과는 candidate hash 순으로 결정적으로 정렬하고, 누락·중복·외부 후보를
  fail-closed로 거부한다.
- 공개 receipt에는 private payload와 local path를 넣지 않는다.

합성 테스트에서 normal split open 순서는 정확히
`train1 → train2 → train4`이고, 각 split opener는 한 번만 호출됐다. Summary
builder와 candidate evaluator도 각각 한 번만 호출됐으며, test1/test2/label/
held-out access counter는 모두 0이었다.

## 의도적으로 구현하지 않은 것

다음 과학적 producer 의미는 아직 외부 동결 authority가 없으므로 추측하지 않았다.

- `EXP02-BIND-QUANTILE`
- `EXP02-BIND-RELATION-SUMMARY`
- `EXP02-BIND-OPPORTUNITY-CENSUS`

또한 별도 self-hashed V2 confirmed cohort도 아직 필요하다. 따라서 이번 변경은
scientific execution도 numeric-policy 결과도 아니다. Frozen preregistration,
후보 분모 37개, 데이터 split, seed, hyperparameter, 선택 규칙은 변경하지 않았다.

## 계산 자원 판단

이 경로의 예상 병목은 CSV/feature parsing과 relation×row CPU scan이다. 작은
numeric-policy 후보 37개에 GPU를 강제로 적용하지 않는다. 한 번 파싱한 private
normal input과 사전 계산 summary를 공유하고, externally frozen producer가 batch
경계에 연결되도록 하는 것이 현재 가장 안전한 최적화다.

## 다음 실행 조건

1. 별도 V2 candidate/cohort authority를 materialize하고 freeze한다.
2. 위 세 scientific binding을 결과 관찰 전에 freeze한다.
3. 이 batch foundation에 producer callback을 연결한다.
4. normal-only train1/train2/train4 selection을 수행한다.
5. selected numeric policy를 기존 atomic persistence gate로 고정한다.

그 전까지 EXP-02 상태는
`BLOCKED_EXP02_SCIENTIFIC_RUNNER_AND_COHORT_AUTHORITY`를 유지한다.

## 과학적 안전

- scientific execution: 0
- train1/train2/train3/train4 scientific opens: 0
- test1/test2/held-out/label access: 0
- architecture/hyperparameter/seed/data/protocol change: 0
- PILOT V1 change: 0
