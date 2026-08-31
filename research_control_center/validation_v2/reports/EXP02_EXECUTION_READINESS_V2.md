# EXP-02 실행 준비도

## 결론

`BLOCKED_EXP02_SCIENTIFIC_RUNNER_AND_COHORT_AUTHORITY`

이 상태는 numeric policy의 성능 결과가 아니다. 현재 구현은 policy와
custody의 순수 contract를 제공하지만, normal train1~4를 읽고 모든
preregistered policy를 평가한 뒤 선택을 atomic freeze하는 추적 가능한
scientific runner가 없다.

또한 preregistration이 요구하는
`SEPARATE_SELF_HASHED_V2_CONFIRMED_COHORT`가 아직 존재하지 않는다. 기존
PILOT V1 cohort를 묵시적으로 V2 authority로 재사용하거나 cohort 없이
train4 selection을 시작하는 것은 허용되지 않는다.

## 안전 경계

- EXP-02 preregistration은 변경하지 않았다.
- 이 readiness 판단에서 train1~4 scientific payload를 열지 않았다.
- test1/test2/label/held-out/provider 접근은 0이다.
- numeric policy는 아직 선택하거나 freeze하지 않았다.
- 정확한 다음 구현은 V2 candidate/cohort authority materialization,
  scientific runner, atomic selected-policy freeze를 결과 관찰 전에 함께
  freeze하는 것이다.

상세한 self-hashed 근거는 `EXP02_EXECUTION_READINESS_V2.json`에 있다.
