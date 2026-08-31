# EXP-01 실행 준비도 및 fail-closed 처분

## 결론

`GDN_CONTRIBUTION_UNRESOLVED_FAIL_CLOSED`

이 상태는 GDN 기여가 없다는 과학 결과가 아니다. 동결 설계가 요구하는
12개 run, corrected combined-view checkpoint, train4 masking intervention을
완결하는 추적 가능한 실행 진입점이 현재 저장소에 없기 때문에, 부분적인
3-seed 실행으로 결과를 만들지 않은 실행 완결성 처분이다.

전용 VALIDATION V2 환경은 CPython 3.12.13, `torch 2.12.1+cpu`,
`torch-geometric 2.8.0`을 충족한다. dependency 실패가 아니라 전체 실행
orchestration과 checkpoint/intervention persistence의 미완결이 원인이다.

## 과학 경계

- EXP-01 preregistration은 변경하지 않았다.
- normal scientific file은 이 readiness 판단에서 열지 않았다.
- test1, test2, label, held-out, provider 접근은 0이다.
- frozen rule에 따라 GDN은 완전한 근거 없이 primary path에 포함하지 않는다.
- 후속 candidate policy는 `META_PLUS_STAT`만 사용할 수 있다.
- 향후 EXP-01 재시도는 전체 executor를 별도 구현·검증·freeze한 뒤 처음부터
  12-run schedule 전체로 수행해야 한다.

상세한 self-hashed 근거는 `EXP01_EXECUTION_READINESS_V2.json`에 있다.
