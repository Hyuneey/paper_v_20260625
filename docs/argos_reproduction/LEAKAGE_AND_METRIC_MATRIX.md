# Leakage and Metric Matrix

TASK-023 compares ARGOS paper-faithful reproduction policy with the `paperworks` proposed-method policy. It does not change the proposed method's PA-free primary metric policy.

## Policy Matrix

| Item | ARGOS paper-faithful reproduction policy | `paperworks` proposed-method policy |
|---|---|---|
| Train labels | May be used to reproduce ARGOS rule generation behavior on public KPI/Yahoo-style data, because ARGOS prompts include labeled examples. Must be recorded as paper reproduction behavior. | Not used for final test leakage. Training labels must not drive final SWaT rule construction unless explicitly approved by split policy. |
| Validation labels | Used by ARGOS Review Agent to evaluate rule accuracy/regression during training. | Validation may support deterministic verification/refinement only under approved split roles; final test remains sealed. |
| Test labels | Used only for final ARGOS reproduction evaluation, not for prompt/rule generation. Any ARGOS code path that evaluates test during construction must be isolated and documented. | Final test labels are evaluation-only and cannot influence candidates, calibration, verification, thresholds, rule selection, or prompts. |
| Rule selection | ARGOS selects top-k rules by training/validation performance according to its selector path. | Rule selection must be deterministic, provenance-recorded, and cannot use final test labels. |
| Threshold selection | ARGOS code evaluates scores and thresholds as part of its reproduction behavior. If reproduced, threshold selection data source must be explicitly logged. | Thresholds and numeric rule parameters must come from approved normal/calibration artifacts, not final test labels. |
| Detector selection | ARGOS paper selects the base detector with highest training score before Aggregator use. | Detector fusion is not a headline result and is not approved for final claims unless separately scoped. |
| Best iteration selection | ARGOS may report or select best runs/iterations according to paper code behavior; any train/test use must be documented. | Best iteration, K, thresholds, prompts, or rules must not be selected using final test labels. |
| Event-PA | ARGOS paper uses Event-PA F1 as primary. Reproduction may report it only as paper-faithful reproduction metric. | PA-free metrics remain primary. Point-adjusted metrics, if added, are supplementary only. |
| Point F1 | Can be reported alongside ARGOS metrics for diagnostic comparison. | PA-free point F1 is allowed as a primary or supporting metric under the evaluation protocol. |
| PA-free metrics | Recommended as an additional reproduction diagnostic to compare with `paperworks` policy. | Primary policy for proposed method. |

## TASK-023 Boundary

TASK-023 does not run ARGOS metrics. It only records how future reproduction
metrics must be separated from the proposed-method metrics.

Rules for future ARGOS reproduction:

- Label every Event-PA result as ARGOS paper-faithful reproduction.
- Do not use ARGOS Event-PA as the proposed-method primary metric.
- Keep ARGOS generated Python, prompts, provider metadata, and run logs outside
  production runtime.
- Keep detector-plus-rule reproduction separate from rule-only reproduction.
- Do not use SWaT staging or official SWaT final data for ARGOS reproduction
  until explicitly approved.
