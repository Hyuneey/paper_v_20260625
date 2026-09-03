# Held-out 및 외부 버전 평가 다음 계획

현재 held-out 일반화는 미확인입니다. old OUTER는 custody check에서 byte read 전에 중단되었고 단순 재시도 권한은 없습니다. 기존 HAI 23.05 test1의 14개 시나리오는 개발 결과를 산출하기에는 유용하지만 최종 Recall의 정밀도와 버전 일반화를 주장하기에는 부족합니다. 하나의 공식 시나리오 안에 있는 attack interval이나 intervention을 독립 공격처럼 나누어 수를 늘리지 않습니다.

## 버전별 panel

- HAI 23.05 test1: 기존 14개 시나리오의 `DEVELOPMENT_ONLY` 결과를 그대로 보존하며 다시 열지 않습니다.
- HAI 23.05 test2: 38개 명목 시나리오의 `PRIMARY_HELDOUT` panel입니다.
- HAI 22.04: 58개 명목 시나리오의 `EXTERNAL_VERSION_REPLICATION_1`입니다.
- HAI 21.03: 50개 명목 시나리오의 `EXTERNAL_VERSION_REPLICATION_2`입니다.

비개발 panel의 명목 합계는 146개이지만 동일 분포의 IID 표본으로 간주하지 않습니다. 주 결과는 버전별 P1-eligible Scenario Recall과 정상 false episodes/hour로 분리 보고합니다. eTaP/eTaR/eTaPR F1, scenario coverage, time-to-first-detection, delay, alarm duration, overlap과 incremental FAR는 보조 지표입니다. 하나의 pooled Recall은 주 결과로 사용하지 않습니다.

## 공격 자료 접근 전에 고정할 것

1. panel별 study identity와 preregistration
2. 공식 scenario authority와 outcome-blind P1 eligibility authority
3. 버전별 data/split identity와 normal-only method re-instantiation
4. 최종 method·authority·feature·numeric policy
5. detector와 기존 frozen fusion policy
6. 공식 eTaPR source/parameter와 range conversion
7. durable prediction-before-label gate와 one-shot label lease
8. no-post-result-tuning 및 버전별 reporting plan

DG-05 승인 전에는 test2나 외부 버전 attack payload 및 label을 열지 않습니다. HAI 22.04/21.03은 같은 Rule bytes를 복사하지 않고 각 버전의 정상 데이터만으로 같은 방법을 다시 인스턴스화합니다.
