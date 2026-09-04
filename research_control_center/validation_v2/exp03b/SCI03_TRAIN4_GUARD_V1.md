# SCI-03 — 한 방향 normal guard

train3 hidden 평가 뒤에만 실행한다. 결과는 provider/feedback/retrieval/추가 호출에 반환하지 않는다.
각 train3-confirmed semantic Rule에 대해 selected pooled option과 같은 tuple의 Common pooled option을 비교한다.
두 numeric world는 동일 semantic set과 동일 train4 file/exposure를 사용한다.
각 world의 source activity는 relation-local threshold/tolerance로 생성한 양쪽 물리 방향 event의 source/row union이다.
nearest OTHER physical source 거리를 Formal V4에 넘긴다. 별도의 Rule evaluator를 만들지 않는다.

양쪽 formed≥5, error0, 유효 exposure가 필요하다. 아니면 UNDEROBSERVED/SYSTEM_ERROR로 비보존.
coverage 3종이 Common보다 낮으면 COVERAGE_REGRESSION.
(seconds/hour, episodes/hour, abstain, complexity) 사전식 순서가 Common보다 나쁘면 NORMAL_BURDEN_REGRESSION.

각 Rule을 별도로 guard한다. 1/2개 보존은 PARTIALLY_RETAINED_RULE_SET.
0개 보존은 NO_RULE_AFTER_GUARD이며 provider의 NO_RULE와 같지 않다.
per-rule opportunity count는 중복 제거하지 않는다.
portfolio FAIL은 (file,row) union 후 episode를 구성하고 exposure를 한 번만 센다.
빈 opportunity의 abstain은 undefined이며 우수성 기준을 자동 충족하지 않는다.

