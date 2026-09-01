# EXP-01 독립 결과 QA

상태: `PASS`

## 무결성 확인

- public receipt hash와 scientific result hash를 독립적으로 재생했다.
- 복구 영수증과 실행 영수증의 12개 checkpoint identity와 순서가 일치한다.
- training 재실행은 0회다.
- frozen config, scientific contract, preregistration, `TASK-039D1R` 최적화
  authority가 모두 그대로다.
- focused public/synthetic tests는 39/39 PASS다.
- 공개 결과에는 private path, raw value, score, loss, credential,
  checkpoint byte가 없다.

## 접근 경계

재개 실행은 train1, train2, train3, train4를 각각 한 번 열었다. 중단된 이전
시도까지 포함한 알려진 누적 open은 2/2/2/1이다. test1, test2, held-out,
label, provider 접근은 모두 0이다.

## 과학적 처분

완결된 primary mask의 pair 수는 0이다. 사전등록된 inclusion rule에 따라
`DEMOTE_GDN_TO_ABLATION_AND_USE_META_STAT`를 적용한다. 이는 GDN 일반 성능이나
탐지 성능에 관한 결과가 아니라, 현재 normal-only 후보 기여 조건을 만족하지
못했다는 완결된 inclusion 결과다.
