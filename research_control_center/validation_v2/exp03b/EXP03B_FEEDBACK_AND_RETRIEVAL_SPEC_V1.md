# Bounded feedback와 retrieval

Feedback: proposal hash, failing Rule index, issue code, affected dimension, remaining budget, retrieval authorization.
허용 issue: LOW_SOURCE_SUPPORT, LOW_TARGET_CONSISTENCY, LOW_EFFECT, OPPOSITE_DIRECTION_COMPETES,
HORIZON_UNSUPPORTED, HORIZON_UNSTABLE, RULE_NOT_JUSTIFIED, RULE_SET_INCOMPLETE, NO_RULE_NOT_JUSTIFIED,
NUMERIC_OPTION_UNSUPPORTED, NUMERIC_OPTION_UNSTABLE, EVIDENCE_REFERENCE_INVALID, DUPLICATE_SOURCE_DIRECTION.

repair turn당 최대 한 train2 slice. numeric failure가 있으면 해당 tuple의 37-option table;
그 밖에는 전체 허용 temporal tuple table을 canonical order로 제공한다.
정답 pass/fail marker, best option, correct tuple, train3/train4는 없다.
request/response hash를 결속한다. 다음 호출은 latest proposal+한 feedback+한 slice를 stateless로 전달한다.
T1과 T1-B에는 어떤 verifier feedback도 보내지 않는다.

