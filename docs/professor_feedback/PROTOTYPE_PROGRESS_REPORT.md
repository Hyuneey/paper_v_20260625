# Prototype Progress Report

## Scope and claim boundary

This package summarizes completed, frozen evidence through TASK-035B. It uses
committed aggregate reports only. No new experiment, metric, rule selection,
provider call, detector/fusion run, private-array access, or test access was
performed for this report.

The results are public-KPI validation evidence and synthetic implementation
evidence. They are not SWaT benchmark results, sealed-test results, or thesis
headline results.

## 1. Research question

The working hypothesis is that LLM-generated rules can provide interpretable
anomaly evidence, but unrestricted code generation is not sufficiently
reliable or controllable for the proposed CPS method. Individual rules may be
precise yet cover only a narrow subset of anomalies. Combining rules can widen
coverage, but naive OR composition can create severe false alarms.

The resulting research direction is therefore not “accumulate more generated
rules.” It is to construct bounded relational rules whose evidence,
parameters, acceptance, runtime behavior, and composition are controlled by
deterministic project-owned mechanisms.

## 2. Prototype implementation

The proposed-method skeleton now connects this synthetic path:

```text
graph / evidence / parameter contracts
-> typed delayed-response rule
-> deterministic 20-stage verifier
-> accepted rule and authority hash
-> authorized LLM-free runtime
-> nine-step satisfaction trace
-> deterministic provenance-bound explanation
```

The complete path replays deterministically on predeclared synthetic fixtures.
This establishes contract and runtime plumbing only. It does not establish
learned-graph quality, calibration validity, real-data effectiveness, or
explanation usefulness.

This skeleton is separate from the ARGOS public-KPI experiments. ARGOS remains
a prior-work reproduction target and rule-only baseline; its unrestricted
generated Python is not inherited into the proposed runtime.

## 3. ARGOS execution evidence

One frozen captured ARGOS rule was executed only inside a WSL-native rootless
Podman container. The boundary used a non-root user, disabled container
networking, a read-only root filesystem, dropped capabilities, resource
limits, and values-only mounts. The host wrapper did not import or execute the
generated source.

Four synthetic non-KPI fixtures were run twice in fresh containers. Their
output hashes were deterministic and the E1 runtime gate passed. This is
execution and isolation evidence, not anomaly-detection evidence.

## 4. Generation cohort

The generation study used the OpenAI Responses API with `gpt-5.6-luna` across
10 public KPI series, 50 predeclared anomaly anchors, and 200 independent
one-shot generation slots. It produced 146 container-executable rule artifacts.

| Output budget | Visible response | Rule extraction | Executable rule |
|---|---:|---:|---:|
| 2,000 tokens | 84% | 61% | 55% |
| 6,000 tokens | 100% | 100% | 91% |

The 6,000-token cohort used the same KPI series, anchors, prompts, provider,
model, static policy, and runtime policy. The change was output budget only.
These percentages measure generation operability. They do not measure rule
accuracy or establish a causal model-quality effect of token budget.

## 5. Validation results

### Initial one-rule validation

One frozen rule on one public KPI validation partition produced direct,
PA-free binary diagnostics:

| Precision | Recall | PA-free point F1 |
|---:|---:|---:|
| 0.846 | 0.189 | 0.308 |

This rule was precision-oriented and had narrow anomaly coverage. The held-out
test was not accessed.

### Ten-KPI outer validation

Ten rules per KPI were frozen without label access. Four compositions were
selected on inner data and evaluated once on frozen outer-validation
partitions. Values below are equal-KPI macro averages of direct PA-free
outputs.

| Arm | Precision | Recall | Point F1 | FP / 10k normal points |
|---|---:|---:|---:|---:|
| Best-1 | 0.7178 | 0.4589 | 0.4801 | 22.08 |
| Top-3 OR | 0.5820 | 0.5975 | 0.5360 | 105.56 |
| Coverage-3 OR | 0.3982 | 0.6968 | 0.3320 | 2084.04 |
| All-10 OR | 0.3181 | 0.6993 | 0.3156 | 2242.19 |

Top-3 OR was the best observed trade-off among the four frozen arms: compared
with Best-1 it showed higher recall and F1, with a higher false-positive cost.
This is a descriptive result on one frozen outer-validation design, not proven
superiority.

Coverage-3 exposed the central failure mode. It increased recall but produced
approximately 2,084 false-positive points per 10,000 normal points and reduced
F1. All-10 added little recall beyond Coverage-3 while worsening precision and
F1 further.

## 6. Main interpretation

1. Individual generated rules tend to be narrow and precision-oriented.
2. A small multi-rule composition can improve anomaly coverage.
3. Coverage-maximizing selection can catastrophically increase false alarms.
4. Increasing the composition from three to ten rules provided little
   additional recall and worsened precision and F1.
5. Generation reproducibility and execution reproducibility are different:
   generated rule content is stochastic, while a frozen rule executes
   deterministically under the isolated runtime.
6. The evidence motivates verifier-governed, false-positive-constrained rule
   construction rather than naive rule accumulation.

These findings do not establish multi-rule superiority.

## 7. Limitations

- The experimental data are public KPI series, not SWaT.
- The ARGOS experiment is univariate.
- Outer validation covers ten KPI series.
- Only one provider/model and one prompt family were studied.
- RepairAgent and ReviewAgent effects were not executed.
- No detector baseline was run.
- No detector-rule fusion was run.
- The held-out test remains sealed and unauthorized.
- No physical causality or root-cause claim is supported.
- These are not thesis headline or final benchmark results.

## 8. Decisions requested

Professor direction is requested on four points:

1. Is the current ARGOS reference experimentation sufficient to proceed?
2. Should detector-only and detector-rule fusion validation precede the
   proposed-method experiment?
3. Should the next primary experiment prioritize graph-guided relational rules
   on official SWaT data?
4. Should the contribution emphasize deterministic verification, anomaly-
   anchored evidence curation, false-positive-constrained composition, or the
   combined system framing?

The detailed decision sheet is in
`docs/professor_feedback/PROFESSOR_DECISION_REQUEST.md`.
