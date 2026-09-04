# Agentic disposition — 결과 전 고정

AGENTIC_ADVANTAGE_SUPPORTED는 모두 필요:
feedback ≥3 distinct pairs; train3-confirmed exact repair ≥2 distinct pairs;
T2 semantic majority exact-match pair count ≥T1-B+2;
T2 strict pair F1 ≥T1-B; strict admitted directional micro F1 >T1-B;
train4 portfolio burden(seconds/hour,episodes/hour,abstain) ≤T1-B;
Formal V4 conversion rate ≥T1-B.
비교 denominator가 undefined이면 우수성 기준을 충족했다고 하지 않는다.

primary 전체는 못 만족하지만 train3-confirmed exact repair ≥2 distinct pairs이면
AGENTIC_MECHANISM_SUPPORTED_BUT_ADVANTAGE_LIMITED.
나머지는 AGENTIC_NOT_SUPPORTED.
conditional 지표, formatting-only repair, repeated identical pair를 새 독립 pair처럼 세어 승격하지 않는다.
EXP-03B 뒤 추가 Agentic rescue는 자동 수행하지 않는다. 최종 이름은 DG-04.

