# 평가 범위 확대 변경 요약 V1

상태: `USER_APPROVED_PLAN_CHANGE`  
과학 결과: `NONE_CREATED`  
공격 데이터 접근: `0`

## 이전 계획

- HAI 23.05 `test1`의 14개 연속 공격 구간 단위를 `DEVELOPMENT_ONLY`로 평가했다.
- 이후 HAI 23.05 `test2` 한 번의 held-out 평가를 계획했다.
- 주 보고는 Attack-event Recall과 normal false episodes/hour 중심이었다.

## 확대된 계획

- 기존 14-event 결과와 prediction·metric authority를 그대로 보존한다.
- `HAI23_TEST2_PRIMARY_HELDOUT_V1`을 주 held-out panel로 둔다.
- HAI 22.04와 HAI 21.03을 별도 external-version replication panel로 둔다.
- nominal non-development scenario는 38 + 58 + 50 = 146개이지만 IID 표본으로 간주하지 않는다.
- 주 결과는 버전별 P1-eligible Scenario Recall과 normal false episodes/hour다.
- eTaP/eTaR/eTaPR F1, coverage, delay, overlap은 보조 지표로 분리한다.
- 한 개의 pooled Recall을 주 결과로 만들지 않는다.
- 공격 label을 열기 전에 버전별 P1 eligibility, 방법, metric, prediction custody를 고정한다.
- 각 외부 버전에서는 같은 방법을 normal-only로 다시 인스턴스화하며 같은 numeric Rule bytes를 이식하지 않는다.

## 근거

14개 개발 단위는 최종 Recall의 정밀도와 버전 일반화를 주장하기에 작다. 하나의 공식 공격
scenario를 여러 interval이나 intervention으로 나누어 표본 수를 늘리면 pseudo-replication이
된다. HAI 버전들은 attack morphology와 feature 구조가 다르므로 버전별 결과와 이질성을
그대로 보여주는 편이 더 정직하다. 운영적 성능에는 단순 hit 외에 range quality, coverage,
delay, false-episode 부담이 필요하다.

이 문서는 연구 소유자가 승인한 향후 계획의 변경 기록이다. 새로운 검출 성능 결과나
일반화 근거가 아니다.
