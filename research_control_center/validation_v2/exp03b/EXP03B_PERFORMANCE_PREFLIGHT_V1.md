# 성능 preflight

정상 evidence materialization 완료: train1/2 각 29 pair, 20 semantic tuple, 37 numeric option. column scale 및 candidate-source event map은 split별 캐시를 재사용하며 Formal V4를 다른 evaluator로 대체하지 않습니다. GDN은 각 split 3개 고정 checkpoint inference만 실행했고 재학습하지 않았습니다.
provider execution은 immutable evidence를 읽기만 합니다. train2 검증은 20 tuple ×37 option의 bounded table 조회이며 원시 HAI를 다시 열지 않습니다. train3 set 비교는 고정 cohort dictionary입니다. train4는 각 arm/repeat의 고정 두 numeric world를 실행하며 이벤트를 source별 재사용합니다.
prompt serialization/token profiling은 로컬에서 완료했습니다. 29 request exact size는 TRAIN1_PROMPT_SIZE_PROFILE receipt에, 최대 repair size는 TRAIN2 profile에 있습니다. API 지연/가격의 실제 측정은 수행하지 않았습니다.
reference/optimized equivalence는 frozen quantile와 Formal V4 synthetic regression으로 검사합니다. 정상 과학 결과를 성능 개선 목적으로 재실행하지 않습니다.
