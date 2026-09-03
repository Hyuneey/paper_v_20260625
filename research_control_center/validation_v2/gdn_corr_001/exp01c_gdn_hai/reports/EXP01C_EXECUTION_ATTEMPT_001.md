# EXP-01C execution attempt 001

- 상태: `FAILED_CLOSED_BEFORE_CHECKPOINT`
- 단계: 첫 combined-view seed 11의 첫 training batch target materialization
- 원인: PyTorch CUDA의 median-with-indices 연산이 deterministic-algorithm mode를 지원하지 않음
- 조치: 3-row median을 수학적으로 동일한 `sum - min - max` 연산으로 바꾸고 R2 environment/execution binding을 새로 발급
- checkpoint 생성: 0
- 과학 결과 생성: 0
- test1/label/test2/held-out access: 0
- 이전 binding과 environment receipt는 역사 기록으로 보존
