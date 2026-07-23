# TASK-037D Report

## Status

`passed_error_conditioned_rule_cohort`

TASK-037D generated and audited
`paper_aligned_error_conditioned_one_shot_rules` from frozen TASK-037B
generation errors. It did not select rules, evaluate inner or outer detection
performance, execute fusion, or access a sealed test.

## Frozen execution

- Commit A: `664857f1df5115f186b578ea3f434be8e7f6db77`
- Detector variants: `LSTMADalpha`, `LSTMADbeta`
- Potential detector/KPI/direction cells: 40
- Eligible cells: 34
- Registered one-shot slots: 96
- Provider/model: OpenAI Responses API / `gpt-5.6-luna`
- Output budget: 6,000 tokens
- Retry and replacement calls: 0

The exact pinned ARGOS combined prompt contract was used. FN prompts paired a
detector-FN target with pure-TN contrast. FP prompts paired an anomaly-free
detector-FP target with TP-supported abnormal contrast. All chunks came from
the frozen generation partition.

## Support audit

| Detector | Direction | Eligible cells | Error segments | Error points | Eligible contrast chunks | Slots |
|---|---:|---:|---:|---:|---:|---:|
| LSTMADalpha | FN | 10 | 690 | 6,466 | 335 | 30 |
| LSTMADalpha | FP | 7 | 520 | 923 | 139 | 17 |
| LSTMADbeta | FN | 10 | 728 | 6,554 | 320 | 30 |
| LSTMADbeta | FP | 7 | 506 | 847 | 140 | 19 |

Two FP cells had zero detector FP and were correctly recorded as not
applicable. Four FP cells had detector FP support but fewer than one distinct
valid anomaly-free 1,000-point target chunk; no request was fabricated for
those cells.

## Generation and runtime

All 96 requests returned visible responses. All 96 responses yielded one rule
that passed the frozen static safety audit.

| Detector | Direction | Registered | Static valid | Executable | Distinct executable |
|---|---:|---:|---:|---:|---:|
| LSTMADalpha | FN | 30 | 30 | 28 | 28 |
| LSTMADalpha | FP | 17 | 17 | 17 | 17 |
| LSTMADbeta | FN | 30 | 30 | 23 | 23 |
| LSTMADbeta | FP | 19 | 19 | 15 | 15 |
| **Total** | | **96** | **96** | **83** | **83** |

The 13 runtime failures were retained: 12 target-runtime failures and one
contrast-runtime failure. No failed rule was repaired or rerun. Runtime checks
used the frozen rootless Podman image with network disabled, a non-root user,
a read-only root filesystem, and bounded CPU, memory, process count, and
timeout. Containers received values only.

## Adequacy gate

- Overall executable yield: 83/96 = 86.46% (minimum 70%)
- Eligible cells with at least one executable rule: 34/34 = 100%
- Multi-slot cells with at least two executable rules: 30/31 = 96.77%
  (minimum 80%)
- Executable FN rules: 51
- Executable FP rules: 32
- All registered slots terminal: yes

Every frozen adequacy condition passed.

## Verification

- TASK-037D targeted tests: 16 passed
- TASK-035A/035AR/035B and TASK-037A/037B/037C regressions: 92 passed
- TASK-023 through TASK-031 applicable regressions: passed
- TASK-032A through TASK-032F contract regressions: 106 passed
- TASK-033 and TASK-034 regressions: 32 passed
- Legacy DSL, verifier, and runtime regressions: 35 passed
- All seven TASK-037D JSON report self-hashes verified
- JSON parsing, `compileall`, `pip check`, and `git diff --check`: passed

Broad host discovery retains the existing optional-dependency collection
boundary: host PyTorch is absent for legacy GDN paths, and the unmodified
upstream ARGOS OpenEvolve test requires host scikit-learn. No new failure was
observed outside those collection boundaries.

## Claim boundary

These results establish provider response/extraction yield, static validity,
runtime-contract validity, and balanced detector-error-conditioned cohort
availability. They do not establish directional correctness, anomaly
detection performance, detector-rule improvement, full Aggregator performance,
exact ARGOS reproduction, or sealed-test performance.

TASK-037E remains a separate, unauthorized selection and outer-validation
task. RepairAgent, ReviewAgent, detector retraining, threshold reselection,
inner evaluation, outer evaluation, fusion, and sealed-test access did not
occur.
