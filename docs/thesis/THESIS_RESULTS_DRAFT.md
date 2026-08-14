# Results Draft

The scientific unit for construction comparisons is the relation direction.
All 42 confirmed directions were retained. Provider calls and materialized
proposals are reported separately and are not treated as independent relation
samples.

## 6.1 Candidate discovery

META, STAT, and GDN generated candidate evidence under separate and
non-comparable scoring policies. Each contributed a primary top-20 set; their
unscored union contained 47 distinct source-target pairs. Overlap is
descriptive only and does not establish correctness or method superiority.

| Candidate-discovery quantity | META | STAT | GDN | Union |
|---|---:|---:|---:|---:|
| Primary candidates | 20 | 20 | 20 | 47 distinct |
| Method-only candidates | 8 | 8 | 18 | - |
| META-STAT overlap | 11 | 11 | - | 11 |
| META-GDN overlap | 1 | - | 1 | 1 |
| STAT-GDN overlap | - | 1 | 1 | 1 |
| Three-way overlap | 0 | 0 | 0 | 0 |

META supplied metadata/manual relation evidence, STAT supplied cross-file
lagged change-correlation stability evidence, and GDN supplied upstream-aligned
learned-graph candidate evidence. No merged score or candidate-method winner
was defined.

## 6.2 Normal relation fitting

The arm-blind D1 procedure evaluated 47 candidate pairs, corresponding to 94
directional opportunities. Twenty-five pairs were fit-supported and 22 were
unsupported. At direction level, 45/94 opportunities were supported, 17 were
direction-unstable, and 32 failed the fit gate. All 12 source-parameter
profiles were supported.

| D1 quantity | Overall | META | STAT | GDN |
|---|---:|---:|---:|---:|
| Candidate pairs | 47 | 20 | 20 | 20 |
| Fit-supported pairs | 25 | 16 | 17 | 5 |
| Pair fit-support rate | 53.19% | 80.00% | 85.00% | 25.00% |
| Directional opportunities | 94 | - | - | - |
| Fit-supported directions | 45 | 29 | 33 | 7 |
| Direction-unstable directions | 17 | - | - | - |
| Fit-unsupported directions | 32 | - | - | - |

Origin counts overlap when the same pair was proposed by multiple candidate
methods; the columns are therefore descriptive memberships, not independent
groups.

## 6.3 Relation confirmation

D2 applied one-way train3 confirmation to the 45 D1-supported directions. It
used no parameter retuning, lower-ranked fallback, opposite-direction search,
or alternative-horizon search. Forty-two directions were confirmed and three
conflicted. Confirmed directions covered 23 of the 25 D1-supported pairs.

| D2 quantity | Overall | META | STAT | GDN |
|---|---:|---:|---:|---:|
| Input fit-supported directions | 45 | - | - | - |
| Confirmed directions | 42 | 28 | 32 | 5 |
| Conflicting directions | 3 | - | - | - |
| D1-supported pairs | 25 | 16 | 17 | 5 |
| Pairs with a confirmed direction | 23 | 15 | 17 | 3 |
| Supported pairs without confirmation | 2 | 1 | 0 | 2 |

These are calibration-confirmed normal delayed-response candidates. They are
not causal relations, root causes, runtime rules, or anomaly-performance
results. E1 subsequently materialized 42 construction-evidence records, 42
approved numeric bundles, and 462 deterministic numeric bindings.

## 6.4 Rule-construction validity

T0, T1, and T1-B produced verifier-admissible outcomes for all 42 relation
directions. T2 accepted 39/42 and emitted three `no_rule` outcomes. Thus,
relation-level deterministic validity reached a ceiling for T0, T1, and T1-B.

| Arm | Calls | Materialized proposals | Admissible | Rejected | Parse failures | Accepted relations | no_rule | Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T0 | 0 | 42 | 42 | 0 | 0 | 42 | 0 | 100.00% |
| T1 | 42 | 42 | 42 | 0 | 0 | 42 | 0 | 100.00% |
| T1-B | 126 | 125 | 122 | 3 | 1 | 42 | 0 | 100.00% |
| T2 | 42 | 42 | 39 | 3 | 0 | 39 | 3 | 92.86% |

Model-visible initial requests matched for all 42 relations across T1, the
three T1-B draws, and T2 call 1; mismatches were zero. T0, T1, and T1-B were
completely concordant. Each paired comparison of one of those arms against T2
contained three discordances, all favoring the non-T2 arm, corresponding to a
7.14 percentage-point difference. The supplementary exact two-sided paired
p-value was 0.25.

This endpoint measures verifier-admissibility, not anomaly-detection utility.

## 6.5 Construction robustness and call efficiency

T1 produced 42/42 accepted outcomes using one call per relation. T1-B used
three independent calls per relation. Its cumulative relation yield was
41/42 after call 1, remained 41/42 after call 2, and reached 42/42 after call
3. The extra two stages consumed 84 calls and recovered one relation. A single
call-2 schema-parse failure did not remove the corresponding relation because
its selected call-1 proposal was already admissible.

| T1-B stage | Calls | Admissible | Rejected | Parse failures | Cumulative accepted | Incremental recovery | Selected |
|---|---:|---:|---:|---:|---:|---:|---:|
| Call 1 | 42 | 41 | 1 | 0 | 41 | 41 | 41 |
| Call 2 | 42 | 39 | 2 | 1 | 41 | 0 | 0 |
| Call 3 | 42 | 42 | 0 | 0 | 42 | 1 | 1 |

Across relations, the number with zero, one, two, or three admissible T1-B
proposals was 0, 1, 2, and 39, respectively. Selected calls 1/2/3 occurred
41/0/1 times.

| Arm | Calls | Accepted | Calls per accepted | Accepted per call | Construction-validity/cost position |
|---|---:|---:|---:|---:|---|
| T0 | 0 | 42 | N/A | N/A | Deterministic baseline |
| T1 | 42 | 42 | 1.000 | 1.000 | Non-dominated provider arm |
| T1-B | 126 | 42 | 3.000 | 0.333 | Dominated by T1: equal yield, 84 more calls |
| T2 | 42 | 39 | 1.077 | 0.929 | Dominated by T1: equal calls, three fewer accepted |

This is a construction-validity/provider-call frontier only. It is not a
utility score or winner ranking.

All T2 attempts ended after call 1. The three rejected proposals contained
unsupported variables, were non-repairable under the frozen controller, and
became `no_rule`. Feedback eligibility, revise, retrieve, follow-up generation,
and successful recovery counts were all zero.

| T2 controller quantity | Count |
|---|---:|
| Provider calls | 42 |
| Accepted at call 1 | 39 |
| Non-repairable no_rule | 3 |
| Feedback-eligible rejections | 0 |
| Revise actions | 0 |
| Retrieve actions | 0 |
| Follow-up generations | 0 |
| Successful recoveries | 0 |

Incremental validity benefit of T2 was not observed. Its feedback-recovery
mechanism was not empirically exercised.

## 6.6 Direct-number experiment

All 42 Direct-number responses were structurally complete: missing-number,
parse/nonfinite, and sign-domain violation counts were each zero. Structural
validity did not imply numerical accuracy.

| Numeric role | N | Mean | Median | SD | Q1 | Q3 | P90 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Source step threshold | 42 | 0.6621 | 0.5984 | 0.2529 | 0.4811 | 0.7443 | 0.9938 | 0.2787 | 1.5215 |
| Source stability tolerance | 42 | 1.1381 | 0.4904 | 1.7716 | 0.1728 | 0.9765 | 5.3937 | 0.0180 | 5.3937 |
| Target noise scale | 42 | 39.6043 | 0.9839 | 92.6787 | 0.8232 | 28.4537 | 86.5962 | 0.3655 | 524.5772 |

| Numeric role | Error >0.10 | >0.25 | >0.50 | >1.00 |
|---|---:|---:|---:|---:|
| Source step threshold | 42 | 42 | 27 | 2 |
| Source stability tolerance | 32 | 24 | 18 | 8 |
| Target noise scale | 42 | 42 | 40 | 14 |

Values are normalized absolute errors. Quantiles use Hyndman-Fan type 7, and
SD is the population standard deviation over all 42 relations. The result
supports deterministic normal-data calibration for this bounded contract; it
does not establish a universal inability of LLMs to estimate numbers.

## 6.7 Candidate-origin subgroup analysis

Origin memberships were non-exclusive: META contained 28 relations, STAT 32,
and GDN 5. T0, T1, and T1-B accepted every relation in each membership. T2
accepted 28/28 META, 30/32 STAT, and 3/5 GDN-member relations.

| Origin | Eligible | T0 | T1 | T1-B | T2 | T2 no_rule | T1-B rejected / parse |
|---|---:|---:|---:|---:|---:|---:|---:|
| META | 28 | 28 | 28 | 28 | 28 | 0 | 0 / 1 |
| STAT | 32 | 32 | 32 | 32 | 30 | 2 | 2 / 1 |
| GDN | 5 | 5 | 5 | 5 | 3 | 2 | 1 / 0 |

Because memberships overlap and GDN has only five relations, candidate-origin
effects remain `INCONCLUSIVE`. The data do not support an ordering such as
META > STAT > GDN.

## 6.8 Utility evaluation boundary

Downstream labeled utility was scientifically motivated because deterministic
validity saturated for three arms and cannot measure attack coverage,
false-alarm burden, duplicate firing, or detector benefit. A post-result,
pre-label protocol was frozen and independently audited. The original audit
identified ten evaluator-authority defects. Bounded remediation closed eight,
but the focused re-audit left two unresolved: the applicable-opportunity /
abstention denominator remained caller-controlled rather than authority-bound,
and some malformed input/state combinations did not fail closed.

The evaluator and execution authorities were therefore not granted. Real HAI
label values accessed, real HAI test-feature values accessed, and real utility
values computed were all zero.

> Utility was scientifically motivated but not evaluated because the
> post-result protocol remained unaudited after the bounded remediation and
> focused re-audit cycle.

This is an evaluation boundary, not a negative utility result. No utility
performance table belongs in this Results chapter.
