# ARCH-000 Result Lineage

No scientific result was recomputed. Each chain was reconstructed from pinned source and frozen public-safe metadata.

## D0

- **SOURCE CODE:** `src/paperworks/v6/task039e3_r2r_d0_inner_execution_v1.py`
- **ENTRYPOINT:** `execute_authorized_d0_inner_v1`
- **INPUT AUTHORITY:** Frozen D0 preprocessing/model/threshold plus exact test1 feature authority; private values not inspected here.
- **PREDICTION ARTIFACT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json`
- **LABEL ACCESS ORDER:** PERSISTED_PREDICTION_BEFORE_LABEL; state machine rejects label access before PREDICTION_FROZEN and metrics reload persisted prediction bytes.
- **METRIC IMPLEMENTATION:** task039e3_r2r_d0_inner_execution_v1.metric_arithmetic_v1 plus task039e3_r2r_utility_evaluator_metrics_v1 episode policy
- **RESULT ARTIFACT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_METRICS_V1.json`
- **INTEGRITY AUDIT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_RECEIPT.json`
- **STATUS:** `VERIFIED_SOURCE_TO_AUDITED_RESULT`
- **QUALIFICATION:** No additional qualification.

## D1

- **SOURCE CODE:** `src/paperworks/v6/task039e3_r2r_utility_inner_d1_execution_v1.py`
- **ENTRYPOINT:** `execute_authorized_inner_d1_v1`
- **INPUT AUTHORITY:** COMMON-42 canonical authority plus main and supplemental frozen normal-only numeric authorities and exact test1 feature authority.
- **PREDICTION ARTIFACT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json`
- **LABEL ACCESS ORDER:** LABEL_BLIND_PREDICTION_OBJECT_BUILT_AND_VALIDATED_BEFORE_LABEL; the result-integrity audit reports prediction_frozen_before_label_access=true. Static source does not show the public prediction file being persisted before label access, so documentation must not strengthen this into the D0-style persistent-file ordering claim.
- **METRIC IMPLEMENTATION:** task039e3_r2r_utility_evaluator_metrics_v1 via _build_private_metric_evidence_v1
- **RESULT ARTIFACT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_METRICS_V1.json`
- **INTEGRITY AUDIT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RESULT_INTEGRITY_V1_RECEIPT.json`
- **STATUS:** `VERIFIED_SOURCE_TO_AUDITED_RESULT_WITH_ORDERING_WORDING_QUALIFICATION`
- **QUALIFICATION:** No additional qualification.

## D2 V1

- **SOURCE CODE:** `src/paperworks/v6/task039e3_r2r_d2_inner_execution_recovery_v1.py`
- **ENTRYPOINT:** `execute_authorized_d2_inner_recovery_v1`
- **INPUT AUTHORITY:** Exact frozen D0 and D1 prediction artifacts plus frozen D2 source map; no D0/D1 rerun or rule reevaluation.
- **PREDICTION ARTIFACT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_COMBINED_PREDICTION_ARTIFACT_V1.json`
- **LABEL ACCESS ORDER:** PERSISTED_COMBINED_PREDICTION_BEFORE_LABEL; recovery source freezes and rereads CombinedPrediction before label and metrics.
- **METRIC IMPLEMENTATION:** Original D2 metric policy reused by recovery bridge; D0 reference reloaded from frozen bytes.
- **RESULT ARTIFACT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_METRICS_V1.json`
- **INTEGRITY AUDIT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_RESULT_INTEGRITY_V1_RECEIPT.json`
- **STATUS:** `VERIFIED_SOURCE_TO_AUDITED_RESULT_VIA_AUTHORIZED_RECOVERY`
- **QUALIFICATION:** A map that points only to execute_authorized_d2_inner_v1 is incomplete; the frozen result was completed by the recovery entrypoint after one infrastructure-aborted attempt.

## D2 V2

- **SOURCE CODE:** `src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py`
- **ENTRYPOINT:** `execute_authorized_d2_v2_inner_v1`
- **INPUT AUTHORITY:** Exact frozen D0 and D1 predictions plus frozen source and native-horizon maps; no predecessor rerun or rule reevaluation.
- **PREDICTION ARTIFACT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_COMBINED_PREDICTION_ARTIFACT_V1.json`
- **LABEL ACCESS ORDER:** PERSISTED_COMBINED_PREDICTION_BEFORE_LABEL; state machine requires COMBINED_PREDICTION_V2_FROZEN before label custody.
- **METRIC IMPLEMENTATION:** task039e3_r2r_d2_v2_inner_execution_v1.compute_metric_values_v1 plus shared episode policy
- **RESULT ARTIFACT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_METRICS_V1.json`
- **INTEGRITY AUDIT:** `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_COMPLETION_V1.json`
- **STATUS:** `VERIFIED_SOURCE_TO_COMPOSITE_INTEGRITY_COMPLETION`
- **QUALIFICATION:** The final PASS is a composite completion record after blocked audit-harness attempts; it did not rerun or modify the frozen scientific result.
