# EXP-05 준비 감사 — Formal V4 trace 기반 설명 구조 일치성

## 1. 판정

**PREPARATION_CONTRACT_IMPLEMENTED_WITH_RUNTIME_CONNECTION_BLOCKED**

EXP-05의 자동 구조 일치성 검증 준비 계약은
`src/paperworks/validation_v2/explanation_fidelity_v1.py`에 구현되었고,
14개 synthetic mutation/conformance test가 통과했다. 그러나 현재
`FormalV4RuntimeTraceV1`만으로 실제 VALIDATION V2 설명을 생성하거나 EXP-05를
과학적으로 실행하면 안 된다.
현재 trace는 `opportunity_id`, `relation_id`, descriptor/authorization/execution-context
hash, terminal `PASS`/`FAIL`/`ABSTAIN`, reason, alarm, trace hash를 기록하지만 다음을
직접 materialize하지 않는다.

- source와 target
- source/target direction
- selected horizon
- 10개 numeric reference ID/hash와 numeric authority hash
- exact observation-window hash와 file-local coordinates
- portfolio/evaluator/trace-contract identity

현재 구현은 위 근거를 담는 `MaterializedFormalV4TraceV1`, 그 trace만 받는
deterministic exact-template renderer, 11개 check의 fidelity validator를 제공한다.
준비 단계의 materializer는 detached pure contract이므로 scientific runner를 승인하지 않는다.
EXP-05 실행 전 마지막 blocker는 evaluated Formal V4 runtime과 **같은 호출 경로에서**
runtime trace와 materialized trace를 함께 생성·저장하도록 연결하고, repository-bound
authorization replay와 durable artifact custody를 그 연결에서 검증하는 것이다.
Canonical `RuntimeTraceV1`로 변환했다고 주장하거나 기존 `ExplanationRecordV1`을 타입만
바꿔 재사용해서는 안 된다. Formal V4와 canonical RuleV1/VerifierV1 authority plane은
서로 다르다.

이 구현과 테스트는 synthetic object만 사용했다. 과학 데이터, test1, test2,
held-out, runtime execution, label, provider를 사용하지 않았다.

### 구현된 준비 계약

- `MaterializedFormalV4TraceV1`: Formal V4 terminal trace, descriptor, portfolio,
  authorization, execution context, ordered 10-role numeric provenance, observation-window
  hash를 public-safe artifact에 결속한다.
- `FormalV4ExplanationRecordV1`: source/target/direction/horizon/outcome과 provenance를
  exact Korean template로만 렌더링한다.
- `FormalV4ExplanationFidelityResultV1`: 11개 preregistered check를 구조화하고
  expected/observed hash와 deterministic replay 결과를 기록한다.
- `EXP05_SCIENTIFIC_RUNNER_AUTHORIZED = False`: 준비 계약이 과학 실행 권한으로
  오인되는 것을 fail-closed로 막는다.

### Synthetic test 결과

- focused tests: **14 / 14 PASS**
- PASS / FAIL / 3개 ABSTAIN template: PASS
- stale portfolio/authorization/context: reject
- descriptor/numeric order/horizon mutation: reject
- 새 변수/숫자/causal text: fidelity FAIL
- renderer/hash/version mutation: deterministic replay FAIL
- runtime/provider/random/time/dynamic execution dependency: 없음

## 2. 현재 source-supported 사실

| 영역 | 현재 구현 | EXP-05 해석 |
|---|---|---|
| V2 실행 authority | `FormalV4AuthorizedRuntimeV1`와 receipt가 portfolio, descriptor set, numeric authority, evaluator, execution context, feature/file/sampling contract를 재검증 | 선택된 V2 authority로 사용 가능 |
| V2 runtime | `execute_formal_v4_rule_v1`가 source trigger, horizon, target response를 deterministic하게 계산하고 `PASS`/`FAIL`/`ABSTAIN` trace를 반환 | evaluated path는 존재 |
| V2 terminal trace | `FormalV4RuntimeTraceV1` | detection/metric terminal reconciliation에는 충분하지만 explanation grounding에는 불충분 |
| D1 metric adapter | `D1OutcomeInputV1`가 trace hash, horizon/decision coordinates, durable prediction receipt를 재검증 | trace/prediction 결속을 재사용할 수 있으나 explanation trace 대체물은 아님 |
| Canonical renderer | `render_delayed_response_explanation` | deterministic, LLM-free, canonical-only 참고 구현 |
| Frozen PILOT V1 관계 | task-specific trace와 canonical `RuntimeTraceV1`은 `NON_EQUIVALENT` | V1을 소급 변환하거나 설명 결과로 재해석하지 않음 |
| Human usefulness | 평가 없음 | 계속 `UNVALIDATED` |

주요 source:

- `src/paperworks/validation_v2/runtime_v1.py` — `FormalV4RuntimeTraceV1`,
  `execute_formal_v4_rule_v1`
- `src/paperworks/validation_v2/formal_v4_authority_v1.py` —
  `FormalV4RuleDescriptorV1`, `FormalV4AuthorizedRuntimeV1`, runtime receipt/replay
- `src/paperworks/validation_v2/metric_contract_v1.py` — `D1OutcomeInputV1`,
  `adapt_d1_alarm_timeline_v1`
- `src/paperworks/contracts/explanation_v1.py` — canonical-only deterministic renderer
- `research_control_center/architecture/06_runtime_trace_explanation/*`
- `research_control_center/architecture/gap_000_pre_validation/GAP_000_EXP05_GATE.md`

## 3. 현재 trace가 설명에 충분하지 않은 이유

### 3.1 terminal hash와 설명 근거는 다르다

현재 trace hash preimage에는 terminal state와 authority identity가 들어가지만 descriptor의
source/target/direction/horizon과 numeric references는 들어가지 않는다. Renderer가 별도로
descriptor를 lookup하면 동일 relation을 사용했다는 점을 다시 입증해야 한다. 그렇지 않으면
stale descriptor나 wrong numeric authority를 결합할 수 있다.

### 3.2 observation window가 trace hash에 직접 묶이지 않는다

현재 trace는 `opportunity_id`만 기록한다. 서로 다른 observation values가 같은 opportunity와
terminal outcome을 만들 때 trace hash만으로 어느 exact window가 평가됐는지 독립 replay할 수
없다. EXP-05 path는 raw values를 공개하지 않으면서도 canonical observation-window hash와
file-local coordinate binding을 materialized trace에 포함해야 한다.

### 3.3 canonical explanation type으로의 단순 투영은 lossless하지 않다

Canonical renderer는 canonical RuleV1, VerifierV1, `RuntimeTraceV1`, nine satisfaction steps,
canonical runtime authorization을 전제로 한다. Formal V4는 별도 descriptor와 authorization을
사용하고 increase/decrease 및 Formal V4 reason taxonomy를 가진다. 형식상 비슷한 필드를
채우는 것은 authority equivalence 증거가 아니다.

## 4. 제안하는 evaluated trace 경로

```text
FormalV4AuthorizedRuntimeV1
+ FormalV4RuleDescriptorV1
+ FormalV4ObservationWindowV1
        |
        | one evaluated entrypoint; no detached reconstruction
        v
FormalV4RuntimeTraceV1
+ exact observation-window hash
+ descriptor and numeric provenance projection
        v
MaterializedFormalV4TraceV1
        |
        | deterministic exact-template renderer
        v
FormalV4ExplanationRecordV1
        |
        | independent field/text/hash replay
        v
ExplanationFidelityResultV1
```

핵심은 runtime trace를 나중에 임의 descriptor와 결합하지 않는 것이다. 새 tracked entrypoint
`execute_and_materialize_formal_v4_rule_v1`가 authorization replay, runtime evaluation,
materialization을 한 경로에서 수행해야 한다. raw values는 materialized public-safe artifact나
설명에 넣지 않고 exact window hash만 남긴다.

## 5. MaterializedFormalV4TraceV1 계약

구현 모듈: `src/paperworks/validation_v2/explanation_fidelity_v1.py`

### 5.1 필수 identity

- `schema_version`, `trace_id`, `self_hash`
- `runtime_version`, `runtime_trace_hash`, `trace_contract_hash`
- `method_id`, `config_id`, `experiment_id`, `portfolio_id`
- `portfolio_authority_hash`, `descriptor_set_hash`
- `authorization_id`, `authorization_hash`, `execution_context_hash`
- `evaluator_contract_hash`, `source_commit`

### 5.2 relation grounding

- `opportunity_id`, `relation_id`, `descriptor_hash`
- `source`, `target`
- `source_direction`, `target_direction`
- `selected_horizon_seconds`
- `relation_binding_hash`, `semantic_execution_hash`

### 5.3 numeric provenance

- `numeric_authority_hash`
- 정확히 10개인 ordered `(numeric_role, reference_id, reference_hash)`
- `raw_numeric_values_embedded=false`

Raw/private numeric values는 explanation trace 또는 문구에 복사하지 않는다. EXP-05는 값 자체가
과학적으로 적절한지 평가하지 않고, authorized provenance를 벗어난 숫자가 설명에 생기지
않는지만 평가한다.

### 5.4 observation and outcome grounding

- `observation_window_hash`
- `feature_contract_hash`, `file_contract_hash`, `sampling_contract_hash`
- `event_index`, `target_response_start_index`
- `final_outcome`, `reason`, `alarm_emitted`
- `labels_accessed=false`, `causal_claim_allowed=false`

`target_response_start_index == event_index + selected_horizon_seconds`를 replay한다. Exact file-local
decision coordinate가 사용되는 scientific runner에서는 metric contract의 `D1OutcomeInputV1`
coordinate binding도 함께 결속한다.

### 5.5 closed outcome/reason matrix

| outcome | reason | alarm |
|---|---|---:|
| `PASS` | `expected_response_observed` | false |
| `FAIL` | `expected_response_not_observed` | true |
| `ABSTAIN` | `incomplete_source_window` | false |
| `ABSTAIN` | `source_not_triggered` | false |
| `ABSTAIN` | `incomplete_target_response_window` | false |

Unknown reason, `FAIL` without alarm, `PASS` with alarm, or system/authority error converted to
`ABSTAIN` must fail closed.

## 6. Deterministic renderer 계약

구현 모듈: `src/paperworks/validation_v2/explanation_fidelity_v1.py`

Renderer input은 validated `MaterializedFormalV4TraceV1` 하나와 renderer contract identity다.
Caller-authored prose, optional free text, current time, random value, label, detector result, fusion
result, network/provider input을 받지 않는다.

`FormalV4ExplanationRecordV1`은 최소 다음을 포함한다.

- trace/descriptor/portfolio/authorization/execution-context hashes
- source, target, source direction, target direction, selected horizon
- ordered numeric reference bindings와 numeric authority hash
- final outcome, reason, alarm
- `natural_language_text`
- `renderer_version`, `renderer_contract_hash`, `artifact_hash`
- `causal_claim_made=false`, `root_cause_claim_made=false`
- `human_usefulness_evaluated=false`

문구는 exact closed template로 생성한다.

- source direction: `step_up`/`step_down` 고정 표현
- target direction: `increase`/`decrease` 고정 표현
- `PASS`: 승인된 horizon에서 기대 방향 response가 관찰됨
- `FAIL`: 승인된 horizon에서 기대 방향 response가 관찰되지 않음
- `ABSTAIN`: 세 reason별 고정 표현

자연어에 허용되는 숫자는 `selected_horizon_seconds` 하나뿐이다. 10개 numeric role의 raw 값은
문구에 쓰지 않고 “승인된 수치 기준”이라고만 표현한다. 변수명은 source와 target만 exact
interpolation한다. 설명 artifact에는 생성 시각을 넣지 않아 동일 input bytes가 동일 output
bytes/hash를 만들게 한다.

## 7. Fidelity validator

구현 모듈: `src/paperworks/validation_v2/explanation_fidelity_v1.py`

각 check는 Boolean 하나로 축약하기 전에 expected/observed identity를 구조화해 기록한다.

| check ID | PASS 조건 | fail-closed 예시 |
|---|---|---|
| `SOURCE_MATCH` | explanation source가 trace source와 exact match | 새 변수, 순서 변경 |
| `TARGET_MATCH` | target exact match | 다른 relation target |
| `SOURCE_DIRECTION_MATCH` | `step_up`/`step_down` exact match | 일반 “변화”로 direction 소실 |
| `TARGET_DIRECTION_MATCH` | `increase`/`decrease` exact match | 반대 방향 |
| `HORIZON_MATCH` | integer와 unit가 trace의 authorized horizon과 일치 | caller number |
| `NUMERIC_PROVENANCE_MATCH` | authority hash와 ordered 10 reference tuple가 동일 | 누락, 중복, reorder, stale hash |
| `OUTCOME_MATCH` | outcome/reason/alarm matrix와 설명 outcome이 동일 | `ABSTAIN`을 정상/PASS로 표현 |
| `NO_NEW_VARIABLE` | text가 exact renderer replay와 같고 interpolation 변수 집합이 `{source,target}` | 제3 변수 삽입 |
| `NO_NEW_NUMBER` | text numeric token multiset이 authorized horizon token과 동일 | threshold/value/시간 추가 |
| `NO_CAUSAL_CLAIM` | exact template replay, 두 claim flag false | cause/root cause 문구 삽입 |
| `DETERMINISTIC_REPLAY` | 독립 두 번의 render/serialize/hash 결과 byte-identical | time/random/order 의존 |

자연어를 blacklist만으로 검사하지 않는다. Validator가 trace로부터 expected structured record와
exact text를 독립 재생성하고 artifact 전체를 비교하면 새 변수·숫자·causal narrative를 동시에
fail closed로 막을 수 있다. Blacklist는 보조 negative test일 뿐 authority가 아니다.

## 8. EXP-05 preregistered evaluation

### 8.1 population과 unit

- population: 고정된 V2 runtime execution에서 실제 emitted된 **모든** materialized trace
- unit: one materialized trace / one explanation pair
- strata: `PASS`, `FAIL`, `ABSTAIN` 및 ABSTAIN reason
- labels: 사용하지 않음
- synthetic mutation cohort: scientific headline과 분리된 contract stress test

실제 cohort에 특정 outcome이 0개이면 예시를 과학 cohort에 인위적으로 추가하지 않는다.
해당 stratum은 `NOT_OBSERVED_IN_EVALUATED_COHORT`로 보고하고 synthetic tests에서만 동작을
확인한다.

### 8.2 primary metrics

1. `TRACE_MATERIALIZATION_COVERAGE`
   = valid materialized traces / emitted runtime traces
2. `EXPLANATION_STRUCTURAL_FIDELITY`
   = all-check PASS explanations / valid materialized traces
3. 각 11개 check별 pass/fail count
4. `DETERMINISTIC_REPLAY_MISMATCHES`
5. outcome/reason stratum coverage

### 8.3 frozen acceptance rule

- materialization coverage = 100%
- explanation structural fidelity = 100%
- check failure = 0
- deterministic replay mismatch = 0
- unknown/system error collapsed into explanation = 0
- trace/explanation orphan = 0

하나라도 실패하면 EXP-05 result는 `FAIL_STRUCTURAL_FIDELITY`다. 일부 outcome stratum이
관찰되지 않은 것은 구현 실패가 아니라 coverage limitation이며 claim을 해당 observed strata로
제한한다.

## 9. 구현 순서

1. **완료** — canonical observation-window hash와 raw-value 미노출 projection
2. **완료** — materialized trace contract와 self-hash replay
3. **완료** — Formal V4-specific exact-template renderer와 artifact hash
4. **완료** — 11-check fidelity validator와 14개 synthetic negative/conformance tests
5. **남음** — materialized trace/explanation JSON schema와 schema registry freeze
6. **남음** — one-path `execute_and_materialize_formal_v4_rule_v1`을 shared runtime owner가 구현
7. **남음** — repository-bound authorization replay, durable artifact custody,
   duplicate/orphan/order 검사 bundle을 scientific runner에 결속
8. **남음** — implementation commit/config/schema/artifact namespace freeze
9. **남음** — 실제 V2 runtime cohort 실행 후 trace/explanation 저장
10. **남음** — result-integrity audit 후 EXP-05 report 생성

기존 `contracts/explanation_v1.py`는 canonical reference path로 유지한다. EXP-05 구현이 이를
행동 변경하거나 Formal V4 authority라고 재라벨링하면 안 된다.

## 10. 필수 synthetic tests

- `PASS`, `FAIL`, 세 `ABSTAIN` reason의 exact template fixture
- trace self-hash, window hash, descriptor/authorization/context hash mutation
- stale/wrong portfolio, descriptor, relation, numeric authority
- source/target/direction/horizon mutation
- numeric reference 누락, reorder, duplicate, wrong hash
- event/response-start horizon mismatch
- outcome/reason/alarm 불가능 조합
- 제3 변수, 추가 숫자, causal/root-cause text mutation
- caller-authored text 및 unknown template version 거절
- detector/fusion/label field 주입 거절
- serialization key order와 input tuple order에 대한 deterministic replay
- duplicate trace/explanation, orphan trace/explanation, bundle order mutation
- current-time/random/network/LLM dependency 없음에 대한 static guard
- PILOT V1 path와 canonical renderer byte-preservation regression

## 11. 과학적·주장 경계

EXP-05 PASS가 지지할 수 있는 문장:

> VALIDATION V2의 deterministic explanation artifact는 evaluated Formal V4 trace의
> source, target, direction, horizon, numeric provenance, terminal outcome을 구조적으로
> 재현하며, 고정 template 밖의 변수·숫자·causal claim을 추가하지 않았다.

EXP-05 PASS가 지지하지 않는 문장:

- 설명이 사람에게 유용하거나 이해하기 쉽다.
- `FAIL`이 공격, 원인, root cause를 식별한다.
- 관계가 causal하다.
- 설명이 detector/fusion 판단을 설명한다.
- Rule-only detection이 운영적으로 유용하다.
- test1 구조 일치성이 held-out/generalization을 입증한다.

Human/expert usefulness는 현재 core thesis requirement가 아니며 계속 `UNVALIDATED`다.
EXP-05에는 LLM call, human study, causal counterfactual을 포함하지 않는다.

## 12. 안전·버전 경계

- PILOT V1 artifact와 report는 변경하지 않는다.
- VALIDATION V2 ID/schema/config/artifact namespace를 사용한다.
- test1은 development-only이며 EXP-05 자체는 label-free다.
- test2/held-out은 접근하지 않는다.
- private raw observation/numeric values는 explanation/public artifact에 넣지 않는다.
- runtime/explanation 모두 LLM-free다.
- 구현 commit과 preregistration을 실제 V2 runtime cohort보다 먼저 고정한다.
