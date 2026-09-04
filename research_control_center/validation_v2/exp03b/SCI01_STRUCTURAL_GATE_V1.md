# SCI-01 — split-pure 구조 판정

EXP03B-BIND-001 사용자 승인 명세. 기존 EXP-03/EXP-04/EXP-05 결과를 바꾸지 않는다.

source pre/post 5/5초, 안정성 0.8, refractory 10초, cross-source isolation 2초,
target baseline/response 5/3초, horizon 1/5/10/30/60초를 고정한다.
source normal scale과 screening threshold는 기존 continuous_step_protocol_v1의 단일 파일 함수를 재사용한다.
최소 20개 nontrivial amplitude 조건을 유지한다. 파일 간 differencing은 없다.
구조 isolation은 기존 inclusive ±2초 제외이며, 실제 Rule 결과 판정은 Formal V4만 수행한다.

train1: support ≥5, consistency ≥0.60, robust effect ≥2.0, selected consistency > opposite.
train2: support ≥5, consistency ≥0.60, robust effect ≥1.0, selected consistency > opposite.
각 source direction의 순서는 consistency 내림차순 → effect 내림차순 → support 내림차순 → horizon 오름차순.
train1에 pooled support20/consistency0.70 조건을 적용하지 않는다.

train2 HORIZON_STABLE은 제안 source/target direction에서 통과하는 preferred horizon과 정확히 같은 것이다.
추가 margin은 없다. train2의 구조·numeric 조건을 만족하는 모든 source direction을 포함해야 ACCEPTED이다.
한 방향이라도 누락하면 RULE_SET_INCOMPLETE. 지원 방향이 있을 때 NO_RULE는 NO_RULE_NOT_JUSTIFIED.
feedback은 issue code만 제공하며 정답 tuple을 보내지 않는다.

