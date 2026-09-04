# EXP-03B 의미적 evidence-to-rule induction 실행 결과

판정: **AGENTIC_ADVANTAGE_SUPPORTED**. 다음 사용자 결정은 **DG-04**입니다. 이 문서는 동결된 정상-only 개발 비교 결과이며, 인과적 진실·공격 탐지 성능·held-out 일반화를 입증하지 않습니다. 독립 QA 판정은 별도 `EXP03B_EXECUTION_INDEPENDENT_QA_V1.json`에 결속합니다.

## 고정 설계와 strict 결과

29-pair cohort, stochastic R=3. T0는 한 번만 실행하고 반복표에서는 동일 artifact를 참조했습니다. 반복은 독립 과학 표본이 아닙니다. Primary는 train2-admitted 출력의 semantic majority이며, 실패/no-majority는 고정 cohort 분모에서 오답으로 유지합니다. RAW parsed proposal과 admitted output은 다릅니다. Numeric policy는 provider에 공개하지 않았습니다.

| arm | strict pair P / R / F1 | directional P / R / F1 | exact semantic set | horizon accuracy | selected raw parse | admitted observations |
|---|---|---|---|---|---|---|
| T0 | 5/6 (0.8333) / 5/7 (0.7143) / 10/13 (0.7692) | 14/15 (0.9333) / 28/39 (0.7179) / 56/69 (0.8116) | 18/29 | 28/39 (0.7179) | 29/29 | 20/29 |
| T1 | 9/13 (0.6923) / 3/7 (0.4286) / 9/17 (0.5294) | 17/18 (0.9444) / 17/39 (0.4359) / 34/57 (0.5965) | 12/29 | 17/39 (0.4359) | 87/87 | 38/87 |
| T1-B | 5/7 (0.7143) / 10/21 (0.4762) / 4/7 (0.5714) | 4/5 (0.8000) / 16/39 (0.4103) / 32/59 (0.5424) | 10/29 | 16/39 (0.4103) | 87/87 | 45/87 |
| T2 | 13/15 (0.8667) / 13/21 (0.6190) / 13/18 (0.7222) | 12/13 (0.9231) / 8/13 (0.6154) / 48/65 (0.7385) | 17/29 | 8/13 (0.6154) | 87/87 | 61/87 |

Horizon accuracy는 frozen reference directional relation 분모입니다. Selected raw/admitted는 T0 29 또는 stochastic 87 observation 분모이고, majority valid-output coverage는 JSON의 `strict.valid_output_coverage`에 별도로 기록했습니다. T1-B 전체 draw parse 수와 실패 taxonomy도 JSON에 보존합니다. Conditional metrics는 disposition 판정에 사용하지 않습니다.

## Feedback와 paired 비교

- Initial NEEDS_REPAIR observations: 52
- Feedback actions: 83; distinct pairs: 22
- Verifier repair success observations: 26; distinct pairs: 13
- Train3-confirmed exact semantic repair distinct pairs: 10
- Pair-decision repair distinct pairs: 2
- Paired semantic exact table: T2-only 8, T1-B-only 1, both 9, neither 11.
- Frozen limitation: None

Train3 reference는 `FROZEN_NORMAL_CONFIRMED_RELATION_REFERENCE`입니다. 독립 held-out ground truth가 아닙니다. Formatting repair를 semantic exact repair로 바꾸지 않았습니다.

## Post-induction SCI02B / Formal V4 / train4

모든 provider outputs → train2 admissions → train3 semantic evaluation을 먼저 동결했습니다. 이후 고정 `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05`와 기존 train1/train2 수식·max pooling으로 결속했습니다. Train4는 one-way guard이며 provider 호출이나 proposal 변경으로 돌아가지 않았습니다.

| arm | numeric binding / confirmed eligible | Formal V4 / admitted Rules | retained Rules | false seconds/hour / false episodes/hour / abstain | guard states |
|---|---|---|---|---|---|
| T0 Repeat 1 | 28/28 | 28/30 | 22 | 578/55 (10.5091) / 577/55 (10.4909) / 775/4254 (0.1822) | {"RETAINED": 22, "TRAIN4_COVERAGE_REGRESSION": 4, "TRAIN4_NORMAL_BURDEN_REGRESSION": 2} |
| T1 Repeat 1 | 16/16 | 16/18 | 15 | 120/11 (10.9091) / 120/11 (10.9091) / 229/3547 (0.0646) | {"RETAINED": 15, "TRAIN4_COVERAGE_REGRESSION": 1} |
| T1-B Repeat 1 | 18/18 | 18/24 | 17 | 601/55 (10.9273) / 601/55 (10.9273) / 506/7727 (0.0655) | {"RETAINED": 17, "TRAIN4_COVERAGE_REGRESSION": 1} |
| T2 Repeat 1 | 27/27 | 27/30 | 21 | 527/55 (9.5818) / 526/55 (9.5636) / 1503/8194 (0.1834) | {"RETAINED": 21, "TRAIN4_COVERAGE_REGRESSION": 4, "TRAIN4_NORMAL_BURDEN_REGRESSION": 2} |

이 표는 사전 지정 Repeat 1이며 최선 반복 선택이 아닙니다. 나머지 반복도 JSON에 보존했습니다. Formal V4 conversion의 분모는 frozen evaluator와 동일하게 전체 admitted Rule 수이며, numeric binding 분모는 train3-confirmed eligible 수로 구분했습니다. Opportunity-relation coverage는 frozen aggregate가 보존하지 않아 `NOT_RETAINED_IN_FROZEN_AGGREGATE`입니다. PASS/FAIL/ABSTAIN·unique false seconds·episodes·normal exposure는 JSON portfolio census에 있습니다. Guard 후 빈 portfolio를 provider-proposed NO_RULE로 해석하지 않습니다. Production/held-out Agentic portfolio는 생성하지 않았습니다.

## 호출·token·latency·비용

고정 snapshot `gpt-5.4-mini-2026-03-17`, Responses/default, concurrency1, retry0, T2 ACCEPTED early-stop, 최대3. 첫 과학 호출이 receipt-first probe였으며 추가 probe를 만들지 않았습니다.

| arm | calls | input | output | latency sum / median seconds | uncached standard USD upper |
|---|---|---|---|---|---|
| T1 | 87 | 144,480 | 9,964 | 133.998 / 1.411 | 0.153198 |
| T1-B | 261 | 433,440 | 30,553 | 407.022 / 1.430 | 0.4625685 |
| T2 | 170 | 449,805 | 19,719 | 264.649 / 1.394 | 0.42608925 |

총 518 calls, input 1,027,725, output 60,236, total 1,087,961. 표준 uncached 요금 산식 상한 USD 1.04185575; cached usage 반영 추정 USD 0.64044135. 청구서가 아닌 token-price estimate입니다. [공식 모델 요금](https://developers.openai.com/api/docs/models/gpt-5.4-mini)을 사용했습니다. 승인 hard cap 609 calls / 8,463,360 total tokens / USD11.03을 초과하지 않았습니다.

## 보존과 다음 결정

PILOT V1·EXP-03 V1·V2A39·EXP02·EXP04/05·GDN은 변경하지 않았습니다. Test1 재개봉, test2, held-out, 외부공격, 공격 labels, GDN retraining, post-result tuning, private exposure는 0입니다. Credential은 승인 후 frozen transport에서만 사용했고 값은 기록·공개하지 않았습니다.

DG-04에서 제목·Agentic 기여 범위·construction-arm 표현을 결정합니다. 추가 Agentic rescue는 자동 진행하지 않습니다. DG-05 공격 접근과 DG-06 실제 교수님 제출은 별도 승인입니다. 교수님에게 제출하지 않았습니다.

Result hash: `a187e89e345e9f1eb42ca993c3d53c6f317a8ff5f33ee9fa7c7e8955baa962c8`. Execution source commit: `811d5817bed1484bb3d0c36704bd74f224f4c526`.
