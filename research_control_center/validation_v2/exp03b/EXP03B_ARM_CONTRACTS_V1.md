# Arm 계약

동일 frozen pair cohort, train1 evidence, model snapshot, schema와 출력 제한을 사용한다.

- T0: train1-only deterministic 구조 gate와 numeric option 선택. pair당 1회, provider0.
- T1: pair/repeat당 1회, feedback0.
- T1-B: pair/repeat당 stateless 3회; hidden train2 verifier가 ACCEPTED → NEEDS_REPAIR → REJECTED,
  accepted Rule count 내림차순 → issue count 오름차순 → earlier draw로 선택한다. train3/train4는 선택에 사용하지 않는다.
- T2: proposal → bounded feedback/retrieval → repair, 최대3회.
  ACCEPTED 또는 nonrepairable REJECTED 직후 정지. 네 번째 호출 없음.

RAW_PARSED_PROPOSAL과 TRAIN2_ADMITTED_SCIENTIFIC_OUTPUT을 따로 기록한다.
NEEDS_REPAIR/REJECTED의 parsable proposal은 scientific output으로 인정하지 않는다.
Provider/system/parse/budget/retrieval failure를 NO_RULE로 바꾸지 않는다.
Scientific concurrency=1. R=3은 안정성 관측이며 독립 과학 표본이 아니다.

