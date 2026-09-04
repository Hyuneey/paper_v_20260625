# EXP03B-PAYLOAD-REDUCE-001 — 현재 준비 상태

상태 PREPARED_DG03B_REVISED_PENDING. EXP-03B는 RULE_SET/NO_RULE·source/target direction·horizon만 추론합니다. numeric option은 provider에서 제거했고 모든 출력·train2 admission·train3 평가가 frozen된 뒤 고정 EXP02 policy를 SCI02B로 결속합니다. 기존 SCI01/04와 disposition 기준은 유지합니다.
29 pair, 20 structural rows(+5 GDN horizon rows/STAT), numeric rows740→0. 고정 gpt-5.4-mini-2026-03-17; 최대 609 calls, input 7,216,128, output 1,247,232, total 8,463,360, USD 11.03. 기존80,373,993 input/USD65.90은 historical superseded이며 새 승인으로 사용하지 않습니다.
DG-03B_REVISED 별도 승인 전 provider/credential/probe0. DG-04는 EXP03B 이후입니다. EXP03V1·V2A39·EXP04/05·PILOT 불변; test1/2/heldout/외부공격 접근 없음. Private vault는 SINGLE_COPY_LOCAL_ONLY. 최신 지침: validation_v2/exp03b/EXP03B_PROVIDER_EXECUTION_INSTRUCTION_V2.md.

이 내용은 준비 계약 수정이며 새로운 과학 성능 결과가 아닙니다. 교수님에게 제출하지 않았습니다.

## 이전 기록 — 역사적 보존·현재 승인값 아님

# EXP-03B construct-validity 보정 — 준비 완료

EXP-03 V1은 고정 방향·horizon·numeric reference를 Formal V4 envelope로 만드는 CONSTRAINED_RULE_MATERIALIZATION_BENCHMARK입니다. feedback 0 결과와 모든 수치는 그대로 보존합니다. evidence-to-rule induction 또는 Agentic 우월성을 검증한 결과가 아닙니다.
EXP-03B는 train1 evidence에서 RULE_SET/NO_RULE·방향·horizon·NUM option을 추론하고 train2 hidden verifier의 제한된 feedback을 비교합니다. 29 pair, 37 options, T0/T1/T1-B/T2, R3 (T0는 단일 실행), Repeat1 portfolio 정책. train3 hidden reference 및 train4 one-way guard로 평가합니다.
SCI-01~04 binding과 정상 evidence 준비 완료, provider 호출 0. DG-03B 신규 예산 승인 필요: 고정 gpt-5.4-mini-2026-03-17, 최대609회, 최대USD65.90. DG-04는 EXP03B 결과 이후로 연기합니다. EXP04/05·V2A39-rule·held-out 방법은 변경하지 않습니다. test/공격 접근 및 제출 없음.

## 이전 기록 — 역사적 보존

# EXP-03 고정 snapshot 규칙 구성 비교 결과

상태: COMPLETE_QA_PASS. 모델: `gpt-5.4-mini-2026-03-17`.

| arm | 승인/예정 | 생성 호출 | feedback |
|---|---:|---:|---:|
| T0 | 39/39 | 0 | 0 |
| T1 | 104/117 | 117 | 0 |
| T1-B | 115/117 | 351 | 0 |
| T2 | 105/117 | 117 | 0 |

T2 feedback 0/117; repair NOT_OBSERVED (denominator=0). 자연 cohort에서 feedback이 발생하지 않아 Agentic feedback 이점을 관찰하지 못했다.

## 반복 및 실패 분류

| arm | 반복 1 승인 | 반복 2 승인 | 반복 3 승인 |
|---|---:|---:|---:|
| T1 | 34/39 | 36/39 | 34/39 |
| T1-B | 39/39 | 39/39 | 37/39 |
| T2 | 35/39 | 35/39 | 35/39 |

| arm | 최종 비승인 상태 |
|---|---|
| T0 | 없음 |
| T1 | INTENTIONAL_NO_RULE: 2; PARSE_FAILURE: 9; VERIFIER_REJECTION: 2 |
| T1-B | ALL_DRAWS_FAILED: 2 |
| T2 | INTENTIONAL_NO_RULE: 4; PARSE_FAILURE: 8 |

PARSE_FAILURE는 고정된 strict envelope 검사 실패이며, 모두 JSON 문법 오류라는 뜻은 아니다. T1-B의 ALL_DRAWS_FAILED는 3개 원본 draw 실패를 보존한 terminal 요약이다. operational failure를 no_rule로 바꾸지 않았다.

실제 호출 585회; input 439,845, output 196,425, total 636,270 tokens. 표준요금 상한 계산 USD 1.21379625 (cache 할인 미반영, 청구서 확정액 아님). 상한 819회 / 5,031,936 tokens / USD10.07 이내.

## 해석 경계

이미 확인된 39개 directional relation의 identity·방향·horizon·numeric reference를 고정된 Formal V4 표현으로 구성하는 제한된 과제다. 새 관계 발견이나 numeric 추론, 탐지 성능을 측정하지 않았다. 동일 정답 reference가 입력에 있으므로 높은 승인율 자체는 LLM 또는 Agentic 필요성을 입증하지 않는다. T1-B는 항상 3회 독립 생성 후 최초 admissible 출력을 선택하며 T2는 ACCEPTED_PROPOSAL 직후 중단한다. 세 반복은 같은 관계를 재사용하므로 독립 scientific sample 수로 합산하지 않는다. snapshot·temperature 0.7·top_p 1.0·reasoning none을 고정했지만 API 재호출의 byte-identical 출력을 보장하지 않는다. 여기서 replay는 보관된 응답·판정의 무결성 재검증이다.

synthetic stress 390 fixtures는 terminal/controller 계약 점검이며 provider 호출이 없는 별도 결과다. 자연 cohort의 repair evidence와 합치지 않는다. no_rule appropriateness는 관찰된 계약 범위만 다루며 전문가 유용성을 뜻하지 않는다.

## 보존과 다음 단계

V2A 39-rule portfolio, EXP-02, EXP-04/05, detector/fusion, 향후 held-out 방법 집합은 변경하지 않았다. 이번 task의 test1/test2/held-out/공격 label 접근은 0이다. PILOT V1 3,021개 보존 항목은 그대로다. DG-03은 고정 snapshot으로 승인·실행되었다. **DG-04에서 정지**하며 DG-05 공격 접근과 DG-06 제출은 승인되지 않았다.
