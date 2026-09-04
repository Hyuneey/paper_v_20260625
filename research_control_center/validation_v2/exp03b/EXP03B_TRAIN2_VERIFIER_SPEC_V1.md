# Hidden train2 verifier

SCI01_STRUCTURAL_GATE_V1.md와 SCI02_NUMERIC_OPTION_POLICY_V1.md가 수치 판정 authority다.
schema → fixed pair → evidence reference → 중복/최대2개 → 구조 support/consistency/effect/opposite →
horizon stability → numeric admissibility → Rule-set completeness 순으로 검증한다.
결과는 ACCEPTED/NEEDS_REPAIR/REJECTED. GDN은 hard acceptance에 사용하지 않는다.
pair 변경, 임의 변수/수치/code, privacy 위반, provider/system failure, fourth call은 nonrepairable.
방향/horizon/option/reference/NO_RULE와 RULE_SET completeness는 repairable이다.
train2 GDN retrieval은 TRAIN2_ONLY frozen checkpoint와 해당 purged validation만 사용할 수 있다.

