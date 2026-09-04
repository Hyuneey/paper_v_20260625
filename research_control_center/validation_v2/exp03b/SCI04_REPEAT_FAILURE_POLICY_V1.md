# SCI-04 — 반복·실패·분모

semantic tuple=(source direction,target direction,horizon).
execution tuple은 numeric alias를 추가한다. evidence IDs는 fidelity metadata다.

T0는 pair당 한 번만 실행한다. 반복 표에는 DETERMINISTIC_SINGLE_RUN_REFERENCE로 같은 artifact를 참조한다.
T1/T1-B/T2는 3회. 실제 valid semantic set이 두 번 이상 같을 때만 majority.
NO_RULE는 accepted empty set이다. 실패는 no-vote이며 NO_RULE가 아니다.
두 동일 set+한 실패는 majority; 세 다른 set은 NO_MAJORITY; 전부 실패는 NO_VALID_OUTPUT.
별도로 RULE_SET/NO_RULE top-level majority를 계산한다. field-wise 합성은 금지한다.

정확한 cohort N을 고정한다. no-decision은 positive reference에서 FN, negative reference에서 FP다.
TP/TN으로 세지 않는다. strict full-cohort 지표만 disposition에 사용한다.
conditional valid-output 지표는 denominator를 함께 report-only로 제공한다.
양쪽 empty set은 pair exact match이나 directional denominator에는 기여하지 않는다.
예측 positive가 없고 reference positive가 있으면 precision/recall/F1=0, NO_PREDICTED_POSITIVES.
N=0 또는 reference class가 하나뿐이면 해당 disposition을 fail-closed한다.

REPEAT_1만 prospective T2 Agentic portfolio를 만들 수 있다. best repeat 선택은 없다.
초기 NEEDS_REPAIR → 나중 ACCEPTED는 verifier repair.
train3 confirmed exact repair는 feedback 이후 초기 semantic mismatch가 final admitted exact match로 개선된 경우만 센다.
formatting-only 개선은 과학적 repair가 아니다.

