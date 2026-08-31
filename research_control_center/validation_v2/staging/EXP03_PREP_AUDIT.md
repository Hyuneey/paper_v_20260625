# EXP-03 준비 감사 — Construction / Agentic 비교

## 1. 판정

**PREPARATION_READY_PROVIDER_GATED**

EXP-03의 구현 전 계약과 실험 설계는 고정할 수 있다. 그러나 새 provider 호출은 아직
허가되지 않았다. 자연 cohort의 실제 실행은 `DG-03`에서 provider, model snapshot,
최대 호출 수, 최대 token budget, 공개 가능한 입력 projection, 결과 artifact를 사용자가
승인하기 전까지 금지한다.

이번 준비 감사는 source·test·기존 sanitized audit만 정적으로 읽었다. provider/LLM 호출,
과학 데이터, test1, test2, held-out, private evidence, 기존 frozen proposal/result를 읽거나
실행하지 않았다.

## 2. 현재 구현에서 확인된 것

### 이미 분리되어 있는 하위 상태

- `task039e3_execution_prep_v1.py`의 parser는 `parsed`, `provider_refusal`,
  `incomplete_response`, `schema_parse_failure`를 구분한다.
- transport 실행은 retryable transport failure와 terminal response를 구분하고,
  append-only call ledger와 failure receipt를 가진다.
- task validity는 `admissible`, repairable rejection, non-repairable rejection을 구분한다.
- T2 controller는 `revise`, `retrieve`, `no_rule`을 결정론적으로 선택하고 최대 세 번의
  generation call 뒤에는 네 번째 호출을 거부한다.
- `outcomes_v1.py`의 일반 v6 contract는 `NO_RULE`, `PROVIDER_ERROR`, `INVALID_OUTPUT`,
  `NON_REPAIRABLE_REJECTION`, `BUDGET_EXHAUSTED`를 구분한다. 특히 `NO_RULE`이
  provider/output failure를 대신할 수 없도록 막는다.

### EXP-03 전에 닫아야 하는 gap

현재 task-specific `ConstructionOutcomeRecordV1`의 최상위 `outcome`은
`accepted_proposal | no_rule`뿐이다. 따라서 다음 원인이 최종 집계에서 같은
`no_rule` headline으로 합쳐질 수 있다.

- provider refusal 또는 missing response
- incomplete/empty response
- strict schema parse failure
- verifier rejection
- non-repairable issue
- repairable issue 이후 budget exhaustion
- T1-B의 세 draw가 모두 실패한 경우

retrieval integrity failure와 local system failure는 exception/failure receipt 경로로 남지만,
relation 단위 terminal artifact에 완전하게 정규화되지 않는다. 하위 ledger만으로 사후 원인을
복원하는 방식은 EXP-03의 주 결과 계약으로 충분하지 않다.

과거 PILOT V1의 세 T2 `no_rule`은 sanitized evidence상 unsupported-variable validity
rejection으로 해석 가능하지만, 이 사실은 일반 conflation을 해결하지 않는다. V1 artifact는
그대로 보존하고 V2에서만 새 taxonomy를 사용해야 한다.

## 3. V2 terminal taxonomy

모든 relation × arm × repeat는 아래 terminal class 중 정확히 하나를 가진다. 성공 결과는
별도 `ACCEPTED_PROPOSAL` 상태로 둔다. 아래 아홉 class는 실패/비생성 결과의 exhaustive하고
mutually exclusive한 분류다.

| terminal class | 정확한 조건 | `no_rule`로 집계? | 필요한 근거 |
|---|---|---:|---|
| `INTENTIONAL_NO_RULE` | bounded construction contract가 유효한 no-rule 선택을 명시하고, 허용된 evidence-grounded reason이 검증됨 | 예, semantic no-rule로만 | no-rule response hash, reason code, evidence ref, validator result |
| `UNSUPPORTED_EVIDENCE` | proposal 전에 deterministic evidence eligibility가 불충분/불안정으로 판정되어 construction이 열리지 않음 | 예, evidence no-rule로만 | evidence status, eligibility policy hash, reason code |
| `PROVIDER_ERROR` | transport/provider error, refusal, HTTP terminal failure 또는 retry exhaustion | 아니오 | attempt ledger, response/receipt hash, provider classification |
| `EMPTY_RESPONSE` | transport는 성공했으나 structured payload가 없거나 finish condition 때문에 완결 payload가 없음 | 아니오 | response hash, finish reason, parser status |
| `PARSE_FAILURE` | non-empty response가 JSON/strict schema/closed-field contract를 통과하지 못함 | 아니오 | response hash, parser issue code |
| `VERIFIER_REJECTION` | parsed proposal이 deterministic verifier에서 거절되고 허용된 repair path가 없거나 해당 arm이 repair를 허용하지 않음 | 아니오 | proposal hash, verifier result hash, repairability |
| `BUDGET_EXHAUSTION` | repairable 상태였으나 고정 call/token budget을 모두 사용하여 더 진행할 수 없음 | 아니오 | budget policy, calls/tokens used, prior verifier results |
| `RETRIEVAL_FAILURE` | T2의 same-corpus targeted re-presentation이 identity/integrity/availability 계약을 통과하지 못함 | 아니오 | retrieval request/receipt, requested identity, failure code |
| `SYSTEM_ERROR` | local invariant, persistence, serialization, unexpected exception 또는 custody failure | 아니오 | fail-closed system receipt와 exception class |

중요한 mapping 규칙:

1. provider가 존재하지 않는 변수를 제안하여 verifier가 거절하면
   `UNSUPPORTED_EVIDENCE`가 아니라 `VERIFIER_REJECTION`이다.
2. `INTENTIONAL_NO_RULE`과 `UNSUPPORTED_EVIDENCE`만 semantic no-rule 지표의 분자가
   될 수 있다.
3. T1-B의 세 draw가 서로 다른 원인으로 실패하면 draw별 terminal class를 모두 보존하고,
   arm terminal은 고정 precedence가 아니라 `ALL_DRAWS_FAILED` summary와 draw refs를 가진다.
   headline 분석은 draw-level 분포와 arm-level accepted 여부를 따로 보고한다.
4. system/provider failure가 발생한 relation을 accepted-yield denominator에서 조용히 빼지 않는다.
   전체 scheduled count, scientifically evaluable count, system-failed count를 각각 보고한다.
5. run-level custody/authority failure는 relation별 `SYSTEM_ERROR`를 대량 생성하지 않고 run을
   fail-closed 중단한다.

## 4. cohort 분리

### A. Natural construction cohort

- 입력은 EXP-01/EXP-02 뒤에 별도 ID로 freeze된 VALIDATION V2 relation/evidence cohort다.
- 공격 label, detector result, test1/test2/held-out, 다른 arm의 결과를 construction input에
  넣지 않는다.
- artificial proposal fault, parser fault, transport fault를 주입하지 않는다.
- T0/T1/T1-B/T2의 scientific comparison과 Agentic benefit 판단은 이 cohort만 사용한다.
- 자연 cohort에서 feedback action이 0이면 결론은
  **“bounded feedback capability는 구현되어 있으나 feedback benefit은 입증되지 않았다.”**
  이다.

### B. Preregistered fault-injection stress cohort

- public synthetic fixtures만 사용하고 provider call은 0이다.
- 아홉 terminal class, revise, retrieve, budget exhaustion, wrong identity, partial/missing
  response, parser rejection, fail-closed system path를 한 번 이상 강제로 exercise한다.
- 목적은 taxonomy/classifier/controller/custody contract test다.
- stress recovery rate를 natural Agentic benefit 또는 rule quality로 보고하지 않는다.
- natural과 stress 결과는 artifact namespace, table, headline, denominator를 합치지 않는다.

## 5. T0 / T1 / T1-B / T2 fairness contract

| 항목 | T0 | T1 | T1-B | T2 |
|---|---|---|---|---|
| evidence/cohort | 동일 frozen V2 input | 동일 | 동일 | 동일 |
| provider/model | 해당 없음 | 동일 snapshot | 동일 snapshot | 동일 snapshot |
| initial prompt/schema | deterministic template | 동일 initial prompt family | T1과 동일한 initial request를 3회 독립 생성 | call 1은 T1과 동일; 이후 bounded follow-up |
| generation budget/relation | 0 | 1 | 정확히 3 | 최대 3 |
| feedback | 없음 | 없음 | 없음 | verifier issue만 `revise`/`retrieve` |
| early stop | deterministic outcome | call 1 뒤 종료 | 금지; 3회 모두 수행 후 가장 낮은 admissible index 선택 | accepted/non-repairable/system terminal에서 종료 |
| numeric authority | 동일 frozen refs | 동일 | 동일 | 동일; 새 numeric evidence retrieval 금지 |

Fairness는 “실제 call 수가 항상 동일”이 아니라 T1-B와 T2에 같은 최대 generation
opportunity(3)를 주는 budget-matched design이다. T2가 call 1에서 성공하면 실제 비용은
작을 수 있으므로 maximum budget과 actual calls/tokens/latency를 모두 보고한다.

LLM arm은 temperature `0.7`, seed 없음, stateless request를 사용한다. bitwise deterministic
claim은 금지한다. model/provider/prompt/schema/sampling hash가 repeat 사이에서 같아야 하고,
provider-managed conversation state와 previous response ID는 사용하지 않는다.

## 6. Repeat stability

- natural cohort의 stochastic arm(T1/T1-B/T2)을 `R=3` independent full-cohort repeat로
  preregister한다.
- T0는 한 번 실행하고 같은 input에서 deterministic self-consistency를 contract test로 확인한다.
- repeat마다 new request/response/call ledger identity를 사용하되 method/config/evidence hash는
  고정한다.
- relation-level로 다음을 보고한다.
  - accepted/not-accepted agreement
  - terminal-class agreement
  - accepted relation set의 pairwise Jaccard
  - executable projection equivalence rate
  - first-call admissibility와 eventual admissibility의 repeat dispersion
  - T2 feedback activation, repair success, revise/retrieve 분포
  - actual calls, tokens, latency의 repeat dispersion
- raw text equality는 stability metric이 아니다.
- 자연 negative result나 unstable result를 본 뒤 repeat 수를 늘리지 않는다.

## 7. Preregistered metrics

### Natural cohort primary construction metrics

1. scheduled relation count와 terminal completeness
2. first-call verifier acceptance rate
3. eventual verifier acceptance rate
4. accepted executable projection rate
5. explicit terminal-class distribution
6. T2 feedback activation rate
7. T2 repair success rate = feedback 후 accepted / feedback action이 발생한 relation
8. revise와 retrieve별 conditional repair success
9. semantic no-rule appropriateness
10. actual generation calls, input/output tokens, latency

`no_rule appropriateness`는 다음처럼 분리한다.

- denominator: `INTENTIONAL_NO_RULE` 또는 `UNSUPPORTED_EVIDENCE`로 종료된 사례
- numerator: blinded deterministic evidence/no-rule validator가 같은 semantic no-rule family를
  확인한 사례
- provider, parse, verifier, budget, retrieval, system failure는 denominator에 넣지 않는다.
- denominator가 0이면 0%가 아니라 `NOT_OBSERVED`로 보고한다.

### Secondary metrics

- strict parser success
- unsupported variable/reference proposal rate
- verifier issue-code distribution
- T1-B any-admissible-among-3와 selected index
- accepted outcome당 call/token cost
- repeat stability 지표

Rule utility, D1 detection, attack recall, FAR는 EXP-03 construction metric이 아니다.

### Stress cohort contract metrics

- 9-class fixture coverage
- terminal classifier exact-match
- `no_rule` conflation count(요구값 0)
- revise/retrieve route coverage
- fail-closed mutation/unknown-class rejection
- fourth-call rejection
- stress recovery count(표시명에 반드시 `SYNTHETIC_STRESS_ONLY` 포함)

## 8. Provider budget·privacy·DG-03

자연 cohort relation 수를 `N`, full-cohort repeat 수를 `R=3`으로 두면 provider generation
call의 hard maximum은 다음과 같다.

```text
T1    = R × N × 1
T1-B  = R × N × 3
T2    = R × N × 3 (maximum; actual may be lower)
TOTAL = R × N × 7 = 21N
```

V2 natural cohort가 42개라면 maximum은 882 scientific generation calls다. 이 수치는 cohort가
freeze되기 전에는 예시일 뿐이며 DG-03 brief는 frozen `N`으로 다시 계산해야 한다. synthetic
stress cohort 호출 수는 0이다. EXP-02 diagnostic numeric proposal calls는 EXP-03 budget에 섞지
않는다.

DG-03 전에 반드시 고정할 항목:

- provider와 exact model snapshot 및 availability basis
- exact `N`, `R`, arm별/전체 maximum calls
- tokenizer/model 기준 request별 maximum input/output tokens와 전체 hard token cap
- monetary maximum estimate와 transport retry policy
- prompt/schema/evidence-projection hashes
- receipt-first one-call authorization, sequential call ordering, abort policy
- output artifact namespace와 public/private custody

Model input은 aggregate `ConstructionInputViewV1`에 한정한다. 허용되는 것은 relation identity,
source/target identity와 방향, selected horizon, approved numeric references, bounded normal-only
evidence summary다. 금지되는 것은 raw time-series rows, labels, attacks, detector outcomes,
test1/test2/held-out, local path, credentials, 다른 arm result, private numeric payload다. API key는
승인된 environment/secret store에서 transport layer만 읽고 prompt/artifact/report에 기록하지
않는다.

DG-03는 provider 호출 직전에만 발동한다. model/provider, 최대 calls, 최대 estimated token
budget, privacy assessment, expected artifacts를 한 페이지로 제시하고 승인을 받기 전에는
capability probe와 scientific call을 모두 수행하지 않는다.

## 9. 구현 계획

### Contract

1. V2 전용 `ConstructionTerminalClassV2` enum과 closed terminal record를 만든다.
2. accepted outcome과 아홉 terminal class를 one-of로 강제한다.
3. relation/arm/repeat/draw, input/proposal/verifier/provider/retrieval refs, calls/tokens,
   controller actions, reason codes, artifact hash를 필수로 한다.
4. existing lower ledgers를 lossless하게 terminal record로 project하되 V1 artifacts는 바꾸지
   않는다.
5. unknown reason, class/reason mismatch, provider/system failure의 no-rule 변환을 거부한다.

### Orchestration

1. natural/stress namespace와 `scientific_eligible` flag를 강제한다.
2. T1-B draw-level terminal을 모두 보존한 뒤 fixed selection을 수행한다.
3. T2 retrieval exception을 `RETRIEVAL_FAILURE`, custody/invariant exception을
   `SYSTEM_ERROR` receipt로 materialize하고 fail-closed한다.
4. call/token/latency와 transport attempts를 generation budget과 별도 기록한다.
5. complete schedule assertion으로 skipped relation/arm/repeat를 거부한다.

### Tests

- 아홉 terminal class 각각의 positive/negative synthetic test
- class/reason/flag mismatch와 unknown class rejection
- refusal vs empty vs parse failure 분리
- unsupported proposal variable → `VERIFIER_REJECTION`
- pre-construction insufficient evidence → `UNSUPPORTED_EVIDENCE`
- repairable rejection 3회 → `BUDGET_EXHAUSTION`; call 4 거부
- retrieval wrong identity/second retrieval → `RETRIEVAL_FAILURE`
- T1-B 세 draw 원인 보존과 lowest admissible selection
- T1-B exact 3 vs T2 maximum 3 fairness
- full schedule completeness와 duplicate key rejection
- natural/stress artifact 및 metric 혼합 거부
- raw rows/labels/test/other-arm result/private path key rejection
- provider-disabled default, credential access 0, network contact 0
- repeat ledger identity unique, frozen config/evidence hash 동일
- aggregate metric denominator와 `NOT_OBSERVED` semantics
- mutation/self-hash/partial-write/stale-authority rejection

## 10. 실행 전 gate

EXP-03 provider execution은 다음이 모두 PASS일 때만 DG-03 brief로 이동한다.

- terminal taxonomy 구현·schema·negative tests PASS
- natural/stress namespace separation PASS
- arm fairness/call ledger/repeat schedule freeze PASS
- V2 relation/evidence cohort ID freeze
- provider-visible projection privacy audit PASS
- exact model/provider/call/token/cost cap 준비
- response custody와 no-overwrite artifact path 준비
- independent QA PASS

현재 상태는 **implementation plan complete, provider execution not authorized**이다.

독립 read-only QA는 아홉 terminal class, natural/stress 분리, `21N`
budget 산술(`N=42`이면 최대 882회), T1-B exact-three와 T2 maximum-three
구분, DG-03 선행 차단, 보수적 claim boundary를 확인하여 준비 초안에
`PASS`를 부여했다. 이는 provider/network custody log나 실행 승인이 아니다.
