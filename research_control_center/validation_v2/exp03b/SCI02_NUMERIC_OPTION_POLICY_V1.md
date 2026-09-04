# SCI-02 — 37개 split-local numeric option

Common 1개와 기존 relation-specific 36개 grid를 유지한다.
NUM-000은 Common; NUM-001..036은 기존 grid의 canonical product 순서다.
실제 family/grid mapping과 role 값은 private authority에 보관한다.
최종 EXP-02 selected-policy ID와 V2A numeric reference는 provider에 제공하지 않는다.

source/target noise는 해당 파일 abs(first difference)의 median이다.
source scope quantile은 양의 absolute difference, relation quantile은 source direction의 양의 magnitude로 계산한다.
기존 empirical_linear_quantiles_v1의 q*(n-1) 연산 순서를 그대로 사용한다.
빈 amplitude/nonfinite/비양수 target noise는 materialization 불가로 명시한다.

train1과 train2 각각 동일 tuple의 Common을 comparator로 사용한다.
완전한 finite authority, system error0, formed≥5, retention/opportunity/evaluation coverage 무손실만 eligible.
순서: false seconds/hour → false episodes/hour → abstain → complexity → Common.
같은 relation-specific family 안의 잔여 동일값은 canonical alias 순서로 결정한다.
단일 split에 fit-split variability를 추가하지 않는다.

train2 proposed alias는 train2 preferred alias와 같아야 한다.
다르면 NUMERIC_OPTION_UNSTABLE, eligible option이 없으면 NUMERIC_OPTION_UNSUPPORTED.
둘 다 repairable이며 retrieval은 canonical table 전체를 주되 best marker를 주지 않는다.
train2 ACCEPTED 이후에만 같은 option의 train1/train2 role별 max를 runtime authority로 결속한다.

