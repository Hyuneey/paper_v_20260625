# EXP-02 준비 감사 — 정상 전용 규칙 수치 정책 비교

상태: `PREPARATION_CONTRACT_FROZEN_SYNTHETIC_ONLY`

범위: 정적 코드·감사 근거 검토와 사전등록 초안만 수행

과학 실행: 0

private data 접근: 0

`test1` / `test2` / held-out 접근: 0

provider 호출: 0

## 1. 결론

EXP-02는 구현 준비를 시작할 수 있지만, 현재 숫자 권한의 추적 가능성을 과학적 최적성으로 해석해서는 안 된다. 비교 대상은 다음 두 정책군으로 제한하는 것이 가장 보수적이다.

1. `COMMON_FIXED_NORMALIZED_V1`: 모든 관계에 같은 **무차원 정책과 window 규칙**을 적용하고, 변수 단위만 정상 데이터에서 얻은 scale로 환산하는 공통 고정 기준.
2. `RELATION_SPECIFIC_NORMAL_ONLY_V1`: 같은 정상-only 입력과 닫힌 후보 집합 안에서 관계별 기준을 만들되, `train4` 정상 구간에서 사전등록된 규칙으로 하나를 선택하는 기준.

서로 단위가 다른 P1 변수에 하나의 절대 raw 숫자를 공통 적용하는 설계는 비교 baseline으로 부적절하다. 공통 정책은 raw 값이 아니라 scale multiplier, fraction, horizon/window 후보처럼 단위에 독립적인 기준이어야 한다.

현재 `TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1`은 정상 `train1`·`train2`에서 source threshold, stability tolerance, target noise scale을 결정하고, 나머지 7개 runtime role에는 공통 preregistered constant를 적용한다. 이 정책은 권한과 출처가 잘 결속돼 있지만, 공통 고정 정책과 관계별 정책 중 어느 쪽이 더 안정적이거나 유용한지는 비교되지 않았다.

## 2. 확인된 현재 계약

| 항목 | 확인된 사실 | 근거 |
|---|---|---|
| 정상 수치 fit | `train1` + `train2`만 사용 | `protocol_v1.py::build_validation_protocol_v1`, `derive_source_parameters_normal_only_v1`, `derive_target_scale_normal_only_v1` |
| 정상 policy 선택 | `train4`의 역할은 `NORMAL_POLICY_SELECTION_SANITY` | `protocol_v1.py::SplitRoleV1`, `build_validation_protocol_v1` |
| 개발 평가 | `test1`은 `DEVELOPMENT_ONLY`; policy freeze 뒤 prediction/label metric만 허용 | `ProtocolExecutionGuardV1` |
| 현재 runtime 수치 role | 관계당 10개 role; 3개 data-derived + 7개 frozen constant | `UTILITY_NUMERIC_ROLES`, `CALIBRATION_ROLE_SPECS` |
| horizon | private registry role이 아니라 relation/descriptor에 결속 | `CommonRelationAuthorityV1.selected_horizon_seconds`, `FormalV4RuleDescriptorV1` |
| 현재 source threshold | `max(5 * noise, Q75(nontrivial amplitudes))` | `derive_multi_file_source_parameters_v1` |
| 현재 tolerance | `max(3 * noise, 0.10 * threshold)` | 같은 함수 |
| 현재 target scale | file-local first difference의 pooled robust MAD scale | `derive_multi_file_target_scale_v1` |
| 현재 window 상수 | pre/post 5, stability fraction 0.8, refractory 10, isolation 2, baseline 5, response 3 | `PreregisteredWindowConstantBundleV1`, `_frozen_window_values` |
| 수치 권한과 D0 threshold | 서로 별도 권한 | ARCH-003 |
| 최적성 | 현재 근거로 주장 불가 | ARCH-003, GAP-018 |

현재 구현의 role 값은 source 또는 target 단위로 공유될 수 있다. 따라서 “relation-specific”은 반드시 **관계별 독립 raw literal**을 뜻하지 않는다. V2 구현은 각 값의 공유 범위(`GLOBAL`, `SOURCE`, `TARGET`, `RELATION`)를 명시적으로 기록해야 한다.

## 3. 비교 계약

### 3.1 고정 공통 정책

`COMMON_FIXED_NORMALIZED_V1`은 다음을 만족해야 한다.

- 모든 관계에 동일한 무차원 multiplier/fraction 및 동일 window/event policy 사용;
- source/target 단위 변환에는 정상 `train1`·`train2`에서 산출한 scale만 사용;
- 현재 frozen V1 정책을 V2 identity로 복사하지 않고, 별도 V2 policy/authority ID로 결속;
- relation 후보, 방향, confirmed cohort와 runtime semantics는 relation-specific 정책과 동일;
- raw unit의 공통 absolute threshold 사용 금지.

현재 V1의 공통 공식과 window bundle은 가장 성숙한 comparator 후보지만, V2에서 새 authority로 재생성·검증해야 한다. V1 private registry를 수정하거나 alias하지 않는다.

### 3.2 관계별 정상 전용 정책

`RELATION_SPECIFIC_NORMAL_ONLY_V1`은 다음을 만족해야 한다.

- 수치 후보 생성은 정상 `train1`·`train2`만 사용;
- 후보 공간은 실행 전 완전히 닫히고 hash로 고정;
- 각 후보는 같은 `UTILITY_NUMERIC_ROLES`, unit domain, Formal V4 binding을 충족;
- `train4` 정상 구간에서만 사전등록된 선택 rule을 적용;
- 지원 부족은 값 보간이나 fallback이 아니라 explicit unsupported/retained state로 기록;
- relation, source, target 중 어느 범위에서 값이 공유되는지 기록;
- `test1` 결과를 보고 후보·tie-break·threshold·window를 바꾸지 않음.

`numeric_policy_v1.py`는 결과를 보기 전에 다음 닫힌 후보 공간을 고정한다.

- source threshold noise multiplier: `{3, 5, 7}`;
- nontrivial source-step amplitude quantile: `{Q50, Q75, Q90}`;
- stability noise multiplier: `{2, 3}`;
- stability threshold fraction: `{0.05, 0.10}`;
- Cartesian relation-specific 후보: 정확히 36개;
- target noise multiplier: `1`;
- window/runtime constant: pre/post `5/5`, stability fraction `0.8`, refractory `10`, isolation `2`, target baseline/response `5/3`;
- horizon: 후보 grid에 넣지 않고 별도로 frozen된 `train3` confirmed cohort identity의 Formal V4 horizon을 그대로 유지한다.

공통 기준은 `threshold=max(5×source-scope noise,Q75(source-scope amplitude))`,
`tolerance=max(3×source-scope noise,0.10×threshold)`, `target scale=1×target-scope
robust scale`이다. 관계별 후보는 같은 형태를 relation-local 정상 요약과 위 36개
grid에 적용한다. 두 split의 최종 값은 role별 `max(train1, train2)`로 보수적으로
pool한다. 이 freeze는 과학적 최적성을 주장하지 않으며, train4 결과에 따른 grid
확장을 금지한다.

### 3.3 선택 rule

다음 순서는 구현 전에 고정해야 한다.

1. invalid authority, non-finite 값, 허용 role 누락, unsupported relation을 fail closed로 제외한다.
2. 공통 정책 대비 relation retention, opportunity coverage, evaluation coverage 중 하나라도 낮으면 후보를 부적격 처리한다. 허용 손실은 정확히 `0`이다.
3. 적격 후보 중 `train4` normal false firing을 최소화한다.
4. 동률이면 abstain, split variability, 복잡도 순으로 비교한다.
5. 복잡도는 `COMMON_FIXED_NORMALIZED_V1 < RELATION_SPECIFIC_NORMAL_ONLY_V1 < DIAGNOSTIC_LLM_PROPOSAL_ONLY`로 고정한다. 완전 동률이면 candidate ID lexical order를 적용하므로 공통 기준이 선택된다.

엄격한 `0` 손실 guard는 임의의 허용 오차를 결과에 맞춰 선택하지 않기 위한
보수적 기본값이다. 이후 완화가 필요하면 현재 EXP-02를 수정하지 말고 새 버전과
새 preregistration이 필요하다.

## 4. 사전등록 metric 정의

모든 metric은 policy ID와 authority hash별로 기록한다. 한 개의 종합 “좋음” 점수를 만들지 않는다.

| metric | 제안된 정의 | 선택 사용 | 주의 |
|---|---|---|---|
| `train4_false_alarm_seconds_per_hour` | 정상 `train4`에서 중복 제거된 FAIL second / exact exposure hours | primary | rule record 수와 alarm second를 분리 |
| `train4_false_alarm_episodes_per_hour` | 공통 zero-gap episode builder의 normal false episode / exposure hours | secondary/tie-break | metric contract와 같은 file-local 규칙 사용 |
| `opportunity_coverage` | 형성된 source opportunity가 있는 retained rule / retained rule | guard | zero-opportunity 정책의 0 false alarm 착시 방지 |
| `evaluation_coverage` | `(PASS + FAIL) / (PASS + FAIL + ABSTAIN)` | guard | no-opportunity와 ABSTAIN을 별도 기록 |
| `relation_retention` | complete valid authority와 executable descriptor를 가진 confirmed relation 수 / frozen cohort 수 | guard | false firing을 낮추기 위한 relation 삭제 금지 |
| `abstain_rate` | `ABSTAIN / (PASS + FAIL + ABSTAIN)` | tie-break/report | system error를 ABSTAIN으로 합치지 않음 |
| `fit_split_variability` | 모든 relation-role에 대해 `2×abs(v1-v2)/(abs(v1)+abs(v2))`, both-zero는 0; 그중 최대값 | eligibility/report | relation/file-local 파생값끼리만 비교; cross-file raw differencing 금지 |
| `policy_stability` | 같은 frozen candidate/guard를 정상 partition별로 적용했을 때 eligible set/선택 ID 일치 여부 | report | headline selection에는 사용하지 않음 |

`PROVIDER_ERROR`, parse failure, non-finite data, stale authority, missing role, execution error는 `ABSTAIN`이나 no alarm으로 바꾸지 않고 별도 failure count로 기록한다.

## 5. 권한·freeze 순서

허용 순서는 다음과 같다.

```text
train1/train2 normal inputs
→ candidate policy derivation
→ candidate policy set freeze
→ train4 normal-only selection
→ selected policy/authority receipt atomic freeze
→ V2 portfolio/runtime authorization
→ test1 prediction durable freeze
→ label capability authorization
→ development metric
→ post-label byte identity check
```

금지 순서:

- `test1` result → numeric policy 수정;
- attack label → authority 선택;
- LLM proposal → authoritative value;
- current V1 private registry overwrite;
- `train3`에서 대안 search 또는 재조정;
- failure → `no_rule`, `ABSTAIN`, no alarm coercion.

## 6. 선택적 LLM 진단 arm

기존 `docs/task_reports/TASK-039E0_DIRECT_NUMBER_POLICY.json`은 LLM 직접 수치 제안을 별도 ablation으로 정의하면서 validity/runtime authority를 명시적으로 부여하지 않는다. EXP-02가 이 진단을 포함한다면 다음만 허용한다.

- 별도 `DIAGNOSTIC_LLM_PROPOSAL_ONLY` arm;
- provider 호출 전 DG-03 승인;
- private raw value나 private path를 prompt에 포함하지 않음;
- missing/nonfinite/domain violation 및 approved normal-only authority 대비 normalized absolute error만 보고;
- main policy 선택, verifier acceptance, runtime authorization, D1 prediction에 사용하지 않음.

provider 승인 없이도 main EXP-02는 실행 가능해야 한다. 현재 준비에서는 provider 호출을 수행하지 않았다.

## 7. 권장 구현 모듈과 symbol

공유 계약은 단일 writer가 구현한다. 아래는 새 V2 namespace 제안이며 기존 V1 scientific source는 수정하지 않는다.

| 제안 path | symbol | 책임 |
|---|---|---|
| `src/paperworks/validation_v2/numeric_policy_v1.py` | `NumericPolicyFamilyV1` | `COMMON_FIXED_NORMALIZED_V1`, `RELATION_SPECIFIC_NORMAL_ONLY_V1`, diagnostic-only 구분 |
| 동일 | `NumericRoleScopeV1` | `GLOBAL`/`SOURCE`/`TARGET`/`RELATION` 공유 범위 |
| 동일 | `NumericPolicyCandidateV1` | 완전한 candidate policy, formula/version/config hash |
| 동일 | `derive_common_fixed_policy_v1` | 단위 정규화된 공통 baseline 생성 |
| 동일 | `derive_relation_specific_candidates_v1` | 정상 train1/train2에서만 닫힌 후보 생성 |
| 동일 | `validate_numeric_policy_candidate_v1` | role/domain/authority/split/identity fail-closed 검증 |
| 동일 | `NumericPolicySelectionSummaryV1` | train4 metric과 explicit failures 저장 |
| 동일 | `select_numeric_policy_on_train4_v1` | preregistered guard + lexicographic tie-break |
| 동일 | `NumericPolicyFreezeReceiptV1` | selected policy, input, code, metric, config hash 결속 |
| `src/paperworks/validation_v2/exp02_v1.py` | `prepare_exp02_inputs_v1` | authorized normal input identity만 수용 |
| 동일 | `evaluate_normal_policy_candidate_v1` | train4 normal-only metric 생성 |

현재 `numeric_policy_v1.py`에 구현된 준비 계약은 다음과 같다.

- 별도 self-hashed `train3` confirmed cohort identity;
- common 1개 + relation-specific 36개의 exact candidate set/hash;
- train1/train2-only summary와 exact formula replay;
- exact maximum symmetric split variability;
- train4 `selection_only=True`, `runtime_authority=False`, `labels_allowed=False` authority;
- strict retention/coverage guard와 input-order-independent lexicographic selector;
- empty denominator `UNDEFINED`, system error 별도 상태;
- optional provider diagnostic의 validity/runtime/main-selection authority 상승 거절.

이 모듈은 scientific input adapter, Formal V4 numeric artifact materialization,
atomic selected-policy persistence 또는 test1 runner가 아니다.
| 동일 | `freeze_exp02_selection_v1` | atomic selected-policy receipt 생성 |
| 동일 | `authorize_exp02_test1_development_v1` | protocol/custody 검증 후 test1 development path 승인 |
| 동일 | `build_exp02_result_v1` | normal-only selection과 test1 관찰을 분리한 결과 artifact |

재사용해야 할 현재 symbol:

- `build_validation_protocol_v1`, `validate_validation_protocol_v1`, `ProtocolExecutionGuardV1`;
- `build_policy_freeze_receipt_v1`, `validate_policy_freeze_receipt_v1`;
- `derive_multi_file_source_parameters_v1`, `derive_multi_file_target_scale_v1`, `q75_linear_v1`;
- `FormalV4RuleDescriptorV1`, `FormalV4NumericAuthorityV1`, Formal V4 fail-closed validators;
- durable prediction custody의 atomic persist/reopen/replay/post-label check;
- portable common metric contract의 alarm second/episode/exposure adapters.

## 8. 필수 synthetic test

새 test는 private/scientific data 없이 작성한다.

1. train3/test1/test2/held-out가 numeric fit/selection input으로 오면 거절;
2. `train4`가 candidate derivation에 쓰이면 거절;
3. policy freeze 전 test1 development authorization 거절;
4. test1 결과 뒤 policy mutation·rehash 거절;
5. raw-unit common literal policy 거절;
6. candidate role 누락·추가·중복·non-finite·wrong type 거절;
7. source/target/relation 공유 범위 mismatch 거절;
8. unsupported relation을 no alarm이나 ABSTAIN으로 coercion하면 거절;
9. relation 삭제로 false firing을 낮추는 degenerate candidate 거절;
10. zero opportunity와 zero false alarm을 구분;
11. PASS/FAIL/ABSTAIN/system error를 별도 집계;
12. file-local split variability 계산에서 cross-file difference 금지;
13. selection tie-break 결정성 및 input-order 독립성;
14. authority/config/code/input hash 하나라도 stale하면 거절;
15. optional LLM proposal에 runtime/validity authority 부여 시 거절;
16. selected policy receipt atomic write/reopen/self-hash/mutation 거절;
17. V1 preservation manifest byte identity 유지.

권장 test path:

- `tests/test_validation_v2_numeric_policy_v1.py`
- `tests/test_validation_v2_exp02_v1.py`
- 독립 QA: derivation/selection을 별도 oracle로 재검증하는 `tests/test_validation_v2_exp02_v1_independent.py`

## 9. 실행 전 blocker

| blocker | 상태 | 해소 조건 |
|---|---|---|
| exact relation-specific candidate space 미고정 | `RESOLVED_IN_PREP_CONTRACT` | common 1 + closed 36-point relation grid/formula/hash replay |
| coverage/retention non-inferiority bound 미고정 | `RESOLVED_IN_PREP_CONTRACT` | baseline 대비 strict non-inferiority(허용 손실 0)와 tie-break 고정 |
| V2 numeric authority schema/receipt 미구현 | `BLOCKS_EXECUTION` | Formal V4와 lossless binding, stale rejection synthetic QA PASS |
| train4 authorized input adapter 미구현 | `BLOCKS_EXECUTION` | exact identity, file-local one-second, no label access boundary 구현 |
| EXP-02 scientific runner/result schema 미구현 | `BLOCKS_EXECUTION` | normal selection과 test1 development result를 분리 저장 |
| optional provider call | `DOES_NOT_BLOCK_MAIN_EXP02` | 포함할 경우 DG-03 승인 필요 |
| held-out | `NOT_AUTHORIZED` | EXP-02 범위 밖; DG-05 전 접근 금지 |

## 10. 허용되는 결론

독립 구현 QA는 정상-only derivation, closed 37-policy grid, strict
non-inferiority, deterministic tie-break, cohort/exposure authority binding,
atomic receipt replay, wrong-type 및 stale/mutation 거절을 포함한 20/20
synthetic cases에서 PASS했다. 이는 준비 계약의 구현 근거이며 과학적 선택
결과가 아니다.

실행 후에도 test1은 development evidence다. 허용 가능한 결론은 “사전등록된 정상-only 정책 A가 train4 선택 기준에서 정책 B보다 선택되었고, test1에서는 이러한 개발 관찰을 보였다”까지다.

다음은 허용되지 않는다.

- selected numeric policy가 물리적으로 참이거나 최적이라는 주장;
- test1에서 더 좋은 결과를 보고 일반화/우월성을 주장;
- LLM이 제안한 숫자를 scientific authority로 사용;
- normal association을 causality로 표현;
- PILOT V1 numeric authority를 V2 결과로 재명명.
