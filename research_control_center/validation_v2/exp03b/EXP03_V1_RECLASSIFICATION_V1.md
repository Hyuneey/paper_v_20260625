# EXP-03 V1 측정 대상 재분류 — 결과 보존

분류: `CONSTRAINED_RULE_MATERIALIZATION_BENCHMARK`.
이 문서는 기존 결과 위에 추가한 해석 기록이다. `exp03/execution_v1/` 전체는 변경하지 않는다.

## 무엇을 측정했는가

EXP-03 V1은 이미 고정된 관계를 strict Formal V4-compatible envelope로 표현하는
deterministic/LLM materialization을 측정했다. source/target, 양쪽 방향, 선택 horizon,
승인 numeric reference ID가 입력으로 주어졌다. 따라서 관계 발견, RULE/NO_RULE 근거 추론,
방향·horizon·numeric-policy induction 실험으로 해석하지 않는다.

| provider 입력 | 분류 | 코드 근거 |
|---|---|---|
| source ID / target ID | CANDIDATE_IDENTITY | exp03_live_contract_v1.py:124–140 |
| source direction / target direction | ANSWER_BEARING_STRUCTURE | :130–138 |
| selected horizon | ANSWER_BEARING_STRUCTURE | :130–138 |
| numeric reference IDs | ANSWER_BEARING_NUMERIC_REFERENCE | :138 |
| confirmed relation identity | ANSWER_BEARING_STRUCTURE | :125–139 |
| normal evidence summary hash | NONANSWER_EVIDENCE — 통계가 아닌 identity commitment | :125–132, prompt :36 |
| schema / operator family | FORMAT_CONSTRAINT | :31–59 |
| 실제 numeric 값 | PRIVATE_VALUE_WITHHELD | :35–37 |

코드 경로: `src/paperworks/validation_v2/exp03_live_contract_v1.py`.
prompt는 제공된 필드를 정확히 복사하도록 지시한다. T0도 동일 필드를 복사한다(:143–146).
verifier는 기존 descriptor와 exact equality를 확인한다(:177–205).
수정 가능한 것은 NUMERIC_REFERENCE_MISMATCH뿐이며 방향/horizon 불일치는 terminal이다(:208–219).
NO_RULE는 당시 계약상 허용되지만 근거 기반 무관계 추론의 정확성을 검증한 결과는 아니다.

## 보존할 결과

T0 39/39, T1 104/117, T1-B 115/117, T2 105/117; T2 feedback 0/117.
T2 repair는 NOT_OBSERVED이며 실패 또는 성공으로 재분류하지 않는다.
585개 요청·응답과390개 terminal의 기존 read-only audit 재생 PASS.
result hash: `653ee0d36255e22fcc0a145b9872418aeceac4022c32df71b803db3afe357238`.
call ledger hash: `08176aa65a7bee9e2d442f72c92c2f3b457a72890451da67a53405ee84c9626f`.

기존 DG-04 brief의 current disposition은
`DEFERRED_BY_EXP03B_CONSTRUCT_VALIDITY_CORRECTION`이다. 원본 brief bytes는 유지한다.
이번 재분류는 원래 benchmark 결과 무효화나 기존 V2A/EXP-04/05 수정이 아니다.
