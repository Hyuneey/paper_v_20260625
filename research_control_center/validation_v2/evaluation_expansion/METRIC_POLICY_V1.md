# Evaluation Metric Policy V1

상태: `PREREGISTRATION_PREPARATION_FROZEN`; 공격/label 입력 `0`.

## Primary

- P1-eligible Scenario Recall = detected eligible official scenarios / all eligible official scenarios
- normal false episodes/hour = attack와 겹치지 않는 file-local maximal contiguous alarm episodes /
  normal exposure hours

Exact numerator/denominator와 Wilson 95% interval을 버전별로 보고한다. denominator 0은 0%가
아니라 `NOT_OBSERVED`다.

## Secondary

- eTaP, eTaR, eTaPR F1
- detected scenario count, scenario alarm coverage, median coverage, coverage IQR
- time-to-first-detection, detection delay, alarm episode duration
- detector–Rule overlap, detector miss recovery
- Fusion incremental Recall/FAR
- Rule opportunity/PASS/FAIL/ABSTAIN

Point adjustment, attack-result 기반 grace period, 파일 연결, scenario split은 금지한다. 하나의
official scenario 안에서 여러 interval이 있어도 primary hit는 최대 1이다.

## eTaPR pin

- official upstream: `https://github.com/saurf4ng/eTaPR`
- pinned commit: `af9e7aed35cfd160cbe0d04c8ec4c102502cb677`
- parameters: `theta_p=0.5`, `theta_r=0.1`, `delta=0.0` (official CLI defaults)
- input conversion: file-local ordered range records; no cross-file range
- execution: official implementation 또는 official sample/synthetic fixture에 exact-conformant wrapper
- point-adjusted outputs: 계산되더라도 보고·선택에 사용하지 않음

현재 repository에는 official dependency가 설치되지 않았다. 이번 task는 pin/adapter contract와
synthetic arithmetic만 준비한다. 공격 label 전 별도 environment에서 official fixtures,
wrapper equality, dependency/license, interval inclusivity, performance preflight를 모두 PASS해야
한다. 실패하면 metric environment exchange artifact를 사용하며 metric 자체를 재구현하지 않는다.

## Paired inference

McNemar exact는 같은 version의 완전히 동일한 eligible scenario ID/order를 공유하고 comparison이
label 전 고정된 방법쌍에만 사용한다. discordant count가 0이면 `NOT_OBSERVED`; 작으면 p-value보다
exact discordant table을 우선한다. non-significance를 equivalence로 해석하지 않는다.
