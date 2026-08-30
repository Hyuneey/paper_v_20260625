# V2-PROTOCOL-001 — Validation / Development / Final-Test Contract Freeze

## 판정

`PASS` — VALIDATION V2의 split 역할, 정상-only 선택 경계, test1 개발 평가 순서,
event/episode/FAR 의미, 보고 필드와 실패 동작을 하나의 self-hashed 계약으로 고정했다.
이 작업은 데이터 reader나 metric runner를 실행하지 않았고, future held-out 권한을 만들지 않았다.

- contract source commit: `e014382feeea0ebb69280f11c099645b1ed192b6`
- frozen protocol hash: `2c3000a912caf2167bfe49929c55229e5159d52cc9ad09b7e48d79d9aecc562f`

## Split 역할

| split | V2 역할 | 허용 범위 |
|---|---|---|
| `train1` | `NORMAL_FIT_PRIMARY` | 후보·관계·numeric·detector 정상 fit |
| `train2` | `NORMAL_FIT_SECONDARY` | 독립 file-local 정상 fit 근거 |
| `train3` | `NORMAL_CONFIRMATION_CALIBRATION` | 관계 확인과 D0 threshold calibration |
| `train4` | `NORMAL_POLICY_SELECTION_SANITY` | 정상-only policy 선택과 sanity |
| `test1` | `DEVELOPMENT_ONLY` | policy freeze 뒤 prediction, durable freeze 뒤 label metric |
| `future_heldout` | `FUTURE_FINAL_HELDOUT` | 현재 허용 operation 없음 |

`test2`, `outer`, `heldout`, `sealed` 별칭은 모두 fail-closed다. 실제 held-out study는
DG-05와 새 study identity가 있기 전에는 시작할 수 없다.

## 정책 선택과 label 순서

정책 freeze receipt에는 candidate set, 정상-only selection objective, selection split,
tie-break, selected config, authority, method policy 집합, metric contract와 source commit의
hash identity가 들어간다. Guard는 다음 순서만 허용한다.

1. 정상 fit/confirmation/calibration/selection
2. self-hashed policy freeze receipt 검증
3. `test1` development prediction authorization
4. GAP-FIX-002 durable prediction freeze와 one-shot label capability 발급
5. authority/source/bytes가 재검증된 capability를 이용한 development label metric authorization
6. label access 기록과 완료

raw string operation, bare Boolean freeze assertion, 잘못된 authority capability, 변조된 custody
receipt도 거절한다. 정책 freeze 뒤 fit/selection, label access 뒤 tuning, 중복
prediction/label authorization은 거절한다. 실패는 `no_rule`, no alarm, `ABSTAIN`으로 바꾸지 않는다.

## Event와 metric 의미

- file-local strict one-second, monotonic, no-duplicate/no-missing timestamp 계약
- strict integer label `1`의 maximal contiguous run을 half-open attack-event unit으로 사용
- file 경계를 넘는 event/episode merge 금지
- 같은 file의 event 내부에 alarm second가 하나라도 있으면 hit
- point adjustment, grace window, dilation, minimum duration 없음
- alarm second deduplicate 뒤 gap 0 maximal contiguous episode 구성
- attack과 조금이라도 겹친 mixed episode는 normal false episode numerator에서 전체 제외하고 분할하지 않음
- normal exposure는 strict label `0` row × 1 second
- FAR/hour는 normal false episodes / normal exposure hours
- attack unit 0개 또는 normal exposure 0초인 metric은 0이 아니라 `UNDEFINED`
- D1 `FAIL`만 common alarm이며 `PASS`, `ABSTAIN`, `NO_OPPORTUNITY`는 common no-alarm이다.
  단, system error는 no-alarm으로 변환하지 않는다.

실제 timestamp/alarm adapter와 metric 계산 구현은 다음 task인
`GAP-FIX-METRIC-001`의 범위다.

## 보고와 주장 경계

모든 결과는 protocol/study/evaluation scope, source·data·split·feature·sampling·method·authority,
policy freeze, durable prediction, label authority, metric contract, environment identity를 결속해야 한다.
metric은 numerator, denominator, value, defined flag와 undefined reason을 함께 기록한다.

`test1` 결과는 `DEVELOPMENT_ONLY`다. 통계적 독립 attack-event, final validation,
held-out generalization 주장은 별도 근거 없이는 금지된다.

## PILOT V1 및 안전

PILOT V1 source/artifact/result는 변경하지 않았다. scientific execution, test1/test2/held-out
access, provider call, private exposure는 모두 0이다.
