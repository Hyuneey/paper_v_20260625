# P1 Eligibility Policy V1

## Authority separation

공격 prediction을 만드는 runner는 eligibility나 label을 보지 않는다. 독립 eligibility custodian이
official scenario metadata와 frozen P1 scope를 사용해 opaque authority를 만들고, 모든 방법의
prediction bundle이 durable freeze된 뒤에만 이를 공개한다.

상태는 `P1_ELIGIBLE`, `CROSS_PROCESS_P1_RELEVANT`, `OUT_OF_SCOPE`, `UNRESOLVED`만 허용한다.
Rule 또는 detector가 우연히 발화했다는 이유로 P1 relevant로 바꿀 수 없다.

- HAI 23.05/22.04: official attack target controller/point metadata로 P1 scope를 판정한다.
- HAI 21.03: official process-specific attack metadata를 우선하고, 가능한 target metadata로
  보강한다.

Primary denominator는 `P1_ELIGIBLE` official scenarios다. `CROSS_PROCESS_P1_RELEVANT`는 별도
secondary table, `UNRESOLVED`는 primary denominator 밖에서 reason과 함께 보고한다.

## Event hierarchy

1. LEVEL 1 — official attack scenario: primary statistical unit
2. LEVEL 2 — scenario 내부 contiguous attack interval: secondary description
3. LEVEL 3 — scenario 내부 intervention/response episode: secondary description

Official scenario identities를 복구할 수 없으면 해당 panel은 prediction 전
`BLOCKED_OFFICIAL_SCENARIO_AUTHORITY`로 중단한다. contiguous runs를 동일한 것으로 간주하지
않는다.
