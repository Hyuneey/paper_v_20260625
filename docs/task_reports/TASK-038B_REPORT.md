# TASK-038B Report

Status: `passed_repair_agent_operability_experiment`

TASK-038B executed the bounded RepairAgent component experiment over the
thirteen frozen TASK-037D runtime-failed, static-valid rules. Original
failures were independently replayed before the exact provider-call manifest
was committed. Each reproducibly failed rule was eligible for at most one
RepairAgent revision, with no retry or replacement. Returned rules were
extracted, statically audited, and replayed twice on both target and contrast
values inside the frozen rootless-container boundary. The task reports
executable-rule recovery, provider usage, structural semantic-drift
diagnostics, and A1/A3 branch updates. It does not evaluate ReviewAgent,
detection performance, outer generalization, fusion, or sealed-test
performance.

## Execution Result

| Measure | Result |
|---|---:|
| Frozen Repair population | 13 |
| Reproducible initial failures | 13 |
| Authorized and attempted calls | 13 |
| Captured visible responses | 13 |
| Extracted rules | 13 |
| Static-valid revisions | 13 |
| Deterministic repaired executables | 13 |
| Primary recovery rate | 1.0000 |
| Conditional recovery rate | 1.0000 |

The descriptive Wilson 95% interval for the primary recovery rate is
`[0.7719, 1.0000]`. Formal population inference is not claimed. The result is
classified as `substantial_operability_support`; task completion and Repair
effectiveness remain separate determinations.

Recovered rules comprise nine FN rules and four FP rules: two
`LSTMADalpha` rules and eleven `LSTMADbeta` rules. Twelve target failures and
one contrast failure were recovered.

## Provider Usage

- Input tokens: 72,568
- Cached input tokens: 0
- Output tokens: 13,846
- Reasoning tokens: 3,555
- Total tokens: 86,414
- Automatic retries: 0
- Manual retries: 0
- Replacement calls: 0
- ReviewAgent calls: 0
- Estimated provider cost: `not_computed_unfrozen_pricing`

## Safety Boundary

Generated rules were never imported or executed by host Python. Runtime used
the frozen rootless Podman image with no network, a non-root user, a read-only
root filesystem, dropped capabilities, no new privileges, and bounded CPU,
memory, PIDs, and timeout. Containers received value-only target or contrast
inputs.

No inner label, outer artifact, sealed-test artifact, detector retraining,
threshold selection, ReviewAgent operation, fusion, or detection metric was
used. Raw rules, prompts, responses, values, predictions, errors, receipts,
and private paths remain ignored and untracked.

Structural drift diagnostics describe code changes only. They do not establish
semantic equivalence, scientific validity, detection improvement, outer
generalization, or full ARGOS methodological effectiveness.
