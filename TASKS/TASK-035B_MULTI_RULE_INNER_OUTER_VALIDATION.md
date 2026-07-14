# TASK-035B: Balanced Multi-Rule Inner Selection and Outer KPI Validation

Status: implementation prepared; execution follows the required Commit A / Commit B / Commit C sequence.

The task freezes a label-independent ten-rule panel per KPI, selects four arms on inner data, and evaluates those frozen arms once on outer validation. The test partition remains sealed. See `configs/argos_reproduction/task035b_multi_rule_validation.json` and the protocol documents under `docs/argos_reproduction/`.
