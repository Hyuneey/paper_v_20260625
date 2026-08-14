# Thesis Decision Memo After the Utility Stop

## Recommended thesis position

Frame the thesis as a governed, evidence-bound rule-construction study for
explainable multivariate CPS anomaly detection. The demonstrated result is a
controlled construction-validity comparison with deterministic normal-data
calibration, deterministic admission, and explicit fail-closed behavior. T2 is
an architectural arm with a negative empirical validity result, not the main
superiority claim.

## 1. What did we successfully demonstrate?

The study built an arm-blind evidence pipeline from 47 candidate pairs to 25
fit-supported pairs, 42 confirmed directions, and 42 construction-evidence
records. The construction pipeline produced verifier-admissible outcomes for
42/42 relations under T0, T1, and T1-B and 39/42 under T2. It also demonstrated
one-call T1 feasibility in this cohort, limited T1-B robustness, deterministic
exclusion of three invalid T2 proposals, and strong empirical motivation for
normal-data numeric calibration.

## 2. What did we fail to demonstrate?

We did not demonstrate T2 validity improvement, feedback recovery, candidate-
origin effects, downstream anomaly utility, detector improvement, production
Rule v2/runtime behavior, deployment safety, or an arm winner.

## 3. What contribution remains defensible?

The defensible contribution is the governed separation of relation evidence,
bounded proposal construction, deterministic numeric authority, deterministic
validity admission, explicit `no_rule`, and downstream utility authority. The
experiment supplies empirical evidence at the construction-validity and
calibration layers.

## 4. How should T2 be described?

T2 is a bounded verifier-feedback architecture with explicit fail-closed
behavior. In the observed run it accepted 39/42 relations and emitted three
`no_rule` outcomes. Incremental validity benefit was not observed. Because all
three issues were non-repairable, the feedback-recovery pathway was not
empirically exercised.

## 5. Why is deterministic calibration empirically supported?

The Direct-number arm returned structurally valid values for all 42 relations,
but normalized errors remained substantial. Every source-step-threshold and
target-noise-scale estimate exceeded 0.25 error, and target-noise error had
extreme dispersion. Therefore schema validity did not imply numerical
accuracy, supporting the policy that rules reference normal-derived calibrated
values rather than LLM-invented numbers.

## 6. What does T0 saturation mean?

T0's 42/42 result shows that deterministic template construction already
saturates the current verifier on this cohort. It exposes a discrimination
limit in the validity endpoint. It does not show that T0 has the best anomaly
utility or should be selected as a winner.

## 7. What does T1 and T1-B add?

T1 shows bounded one-call feasibility: one call per relation produced 42/42
admissible outcomes. T1-B shows limited stochastic robustness: it recovered
one first-draw rejection and tolerated one unrelated schema failure, but used
126 calls and did not exceed T1's final yield.

## 8. Why was utility not executed?

Utility required label-aware evaluator authority. A post-result, pre-label
protocol was frozen and audited. After bounded remediation, two issues remained:
the abstention denominator was not bound to enumerated opportunity custody,
and malformed inputs/states could bypass strict fail-closed rejection. The
protocol therefore remained unaudited. The study stopped before accessing
real labels or test features and before computing utility.

## 9. How much does utility absence weaken the thesis?

It substantially weakens any claim about anomaly-detection effectiveness,
false-alarm reduction, detector recovery, or arm usefulness. It does not erase
the construction/governance contribution. A master's thesis remains defensible
if its research questions and headline contribution are narrowed accordingly.

## 10. Which claims must be deleted or softened?

Delete claims of T2 superiority, validated feedback recovery, anomaly utility,
detector improvement, candidate-method superiority, general LLM reliability,
production runtime validation, and any winner. Soften LLM construction claims
to this cohort/model/run and `no_rule` safety claims to deterministic admission
only.

## 11. What is the smallest defensible thesis story?

> Normal-only relation evidence and deterministic numeric references can bound
> a reproducible rule-construction pipeline. Under this frozen HAI P1 cohort,
> deterministic and one-shot construction saturated verifier validity,
> repeated sampling added limited robustness at high call cost, and the
> verifier-feedback arm produced a negative yield result while preserving
> fail-closed admission. Direct numeric generation was structurally valid but
> inaccurate, supporting deterministic calibration. Downstream utility was
> separated by governance and was not evaluated.

## 12. What minimum additional work is necessary?

No new scientific execution is necessary for the narrowed methodological
thesis. The minimum work is editorial:

1. align the title and research questions with construction and governance;
2. replace anomaly-performance wording with verifier-admissibility wording;
3. preserve the negative T2 result and validity ceiling;
4. include the utility stop in Results, Discussion, and limitations;
5. ensure the later abstract uses only the frozen claim inventory; and
6. obtain supervisor/committee agreement that the narrowed contribution meets
   the degree's empirical expectations.

If the thesis must retain a central claim of anomaly-detection effectiveness,
then labeled utility would be necessary. That work is currently unauthorized
and should not be resumed automatically.

## Alternative position

A weaker but still coherent position is a reproducible governance-and-
comparison thesis: it contributes frozen construction arms, deterministic
admission, transactional custody, explicit negative findings, and an auditable
separation between validity and utility.

## Positions to avoid

- T2 is empirically superior.
- Feedback improved or recovered construction.
- T0 or T1 is the useful-rule winner.
- The rules improved anomaly detection.
- Utility failed, was negative, or was zero.
- Another construction rerun or post-hoc metric is needed to rescue the story.

## Decision

Proceed to thesis review with the narrowed construction-governance position.
Do not authorize new scientific work until this memo is reviewed. Do not
automatically resume utility, Rule v2/runtime, or another experiment.
