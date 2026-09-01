# V2-SCI-001 independent QA

Verdict: `PASS`

## 판단

V2-SCI-001 stop condition E에 따라 과학 payload를 열기 전에 fail-closed한
처리가 맞습니다. 동결 run matrix는 다음 네 authority를 실행 전 필수로 규정하지만
현재 존재하지 않습니다.

- `SEPARATE_SELF_HASHED_V2_CONFIRMED_COHORT`
- `EXP02-BIND-QUANTILE`
- `EXP02-BIND-RELATION-SUMMARY`
- `EXP02-BIND-OPPORTUNITY-CENSUS`

## 검증

- focused independent checks: 93 PASS, 1 expected skip
- VALIDATION V2 full suite: 328 PASS, 7 expected skips
- RCC suite: 171 PASS
- Registry/privacy: PASS, new exposures 0
- PILOT V1: 3,021 / 3,021 blobs preserved
- preregistration 변경: 0
- candidate policy 변경: 0
- exact run matrix 변경: 0
- test1/test2/label/held-out/private scientific payload access: 0

## 수정 확인

QA가 지적한 두 traceability 항목을 coordinator가 반영했습니다.

1. Formal V4 evidence hash 옆에 source report path를 기록했습니다.
2. access counter의 scope를 `THIS_V2_SCI_001_ATTEMPT_AFTER_PREFLIGHT`로 명시해,
   과거 정상 train1~train4 custody 접근과 혼동되지 않게 했습니다.

합성 negative path fixture의 privacy scan 오탐 수정은 runtime에서 동일한
절대경로 모양을 계속 검사하며 과학 semantics나 custody behavior를 바꾸지 않습니다.
