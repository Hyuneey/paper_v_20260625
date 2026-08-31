# EXP-01 / EXP-02 exact run matrix freeze

상태: `EXP01_FROZEN_EXP02_SHELL_FROZEN_THREE_SCIENTIFIC_BINDINGS_REQUIRED`

이 문서는 기존 EXP-01·EXP-02 사전등록을 변경하지 않고, 구현과 실행의 정확한 순서 및 파일 소유권을 고정한다. 과학 실행 전 작성되었으며 결과값을 포함하지 않는다.

## 실행 순서

1. EXP-01 전체 12-run 구현과 합성 테스트
2. 구현 독립 QA 및 code/config authority freeze
3. EXP-01 12-run 단독 순차 실행
4. arm-blind train3 confirmation과 train4 fixed-checkpoint intervention
5. 독립 결과 QA
6. 사전등록 inclusion rule에 따른 Candidate Policy freeze
7. V2 confirmed-cohort authority materialization 또는 엄격한 immutable rebind
8. EXP-02 구현 독립 QA 및 code/config authority freeze
9. EXP-02 normal-only train4 선택 실행

EXP-02의 9단계는 다음 세 의미가 결과 관찰 전에 별도 권위로 결속된 뒤에만 실행한다.

- Q50/Q75/Q90의 정확한 보간 알고리즘
- `relation_noise`, `relation_q50/q75/q90`, `relation_target_noise`의 과학적 생산 규칙
- relation-specific threshold에서 opportunity와 cross-source isolation census를 만드는 규칙

현재 Writer 2는 custody·receipt·atomic-freeze shell과 미결속 거절까지만 구현할 수 있다. 이 상태를 EXP-02 실행 완료로 해석하지 않는다.

## 핵심 경계

- EXP-01은 `EXPECTED_SCHEDULE`의 12개 run을 정확히 한 번씩 수행한다.
- run 실패나 누락 시 분모를 줄이지 않는다.
- window는 파일 경계를 넘지 않는다.
- META/STAT는 comparator이며 GDN training run이 아니다.
- META/STAT comparator는 추적된 원본 결과 artifact의 self-hash와 동결 상수를 모두 재생한 경우에만 사용한다. 임의 20-pair 입력은 허용하지 않는다.
- Candidate Policy는 EXP-01 결과 독립 QA 이후에만 동결한다.
- EXP-02는 `SEPARATE_SELF_HASHED_V2_CONFIRMED_COHORT` 없이는 시작하지 않는다.
- rebind는 모든 V2 pair가 기존 arm-blind fit/confirmation universe 안에 있을 때만 허용한다.
- test1/test2/held-out/label/provider는 이 순서 전체에서 금지된다.
- PILOT V1과 동결 사전등록은 수정하지 않는다.

## 사전 선언된 fail-closed 상태

사전등록은 seed 안정성을 `3개 seed 중 2개 이상`으로 정의하지만, 기존 intervention receipt contract는 세 seed에 동일한 mask를 요구하며 각 mask pair가 해당 seed graph에 실제 존재해야 한다. 따라서 최종 primary mask에 정확히 2/3 seed에만 존재하는 pair가 포함되면 구현은 다음 상태로 중단한다.

`EXP01_FROZEN_CONTRACT_CONFLICT_PRIMARY_MASK_2_OF_3_VS_SHARED_ALL_SEEDS`

이 상태에서는 mask를 3/3 pair로 몰래 축소하거나 분모를 줄이지 않는다. EXP-01은 불완전 실행으로 기록되고 GDN 기여는 미확정으로 남으며 Candidate Policy를 동결하지 않는다. 이 fail-closed 처리는 사전등록의 과학 규칙을 바꾸지 않기 위한 실행 안전 규칙이다.

세부 실행표와 namespace 소유권은 함께 동결한 `EXP01_EXP02_EXACT_RUN_MATRIX_V2.json`이 권위다.
