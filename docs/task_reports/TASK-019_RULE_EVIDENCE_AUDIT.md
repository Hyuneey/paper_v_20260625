# TASK-019 Rule Evidence Audit

This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.

## Summary

- Report ID: `e6507dcac0c377e60ef55832af31f9b1f8c8543c9950fcce3badcd1b078b7f2e`
- TASK-018 support scan report ID: `490f741e61409672d42aa5fa784b364053f2d5dc246f2e5f120eb815cc3d5b0d`
- TASK-018 dry-run report ID: `6abb1b90de744a0dfe8f07520f53f66ee2ffd4da967294f8558ff51472f5ba6e`
- Selected loaded range: `[12800, 15912]`
- Selected calibration range: `[13332, 15380]`
- Verified rule evidence cards: 2

## Evidence Cards

### rule.template.4037660c59cbd7f4

- Pair: `MV201 -> AIT201`
- Source metadata: role=`actuator`, value_type=`binary`, stage=`2`
- Target metadata: role=`sensor`, value_type=`continuous`, stage=`2`
- Relation type: `binary_actuator_to_continuous_sensor`
- Trigger/matched/missing/right-censored: 1/1/0/0
- Calibration parameters:
  - `max_response_delay_seconds`: 36.0 seconds (support=1)
  - `min_response_magnitude`: 0.16030000000000655 target_units (support=1)
- Rule AST summary: family=`changed_to_increase_within_response_missing`, trigger=`changed_to`, response=`response_missing(increase_within)`
- Normal false fires: 0 / 33 (0.0)
- Validation coverage: 0 / 8 (0.0)
- Runtime firing count: 0
- Verifier report ID: `a277520aed7ee4ff97ff22847b2d96456dd18090b8aa5d81733d22766b2098da`
- Staging/plumbing artifact only: `true`
- Human-review notes:

### rule.template.ae3f2f7ac58acb79

- Pair: `MV201 -> AIT202`
- Source metadata: role=`actuator`, value_type=`binary`, stage=`2`
- Target metadata: role=`sensor`, value_type=`continuous`, stage=`2`
- Relation type: `binary_actuator_to_continuous_sensor`
- Trigger/matched/missing/right-censored: 1/1/0/0
- Calibration parameters:
  - `max_response_delay_seconds`: 3.0 seconds (support=1)
  - `min_response_magnitude`: 0.00576800000000155 target_units (support=1)
- Rule AST summary: family=`changed_to_increase_within_response_missing`, trigger=`changed_to`, response=`response_missing(increase_within)`
- Normal false fires: 0 / 33 (0.0)
- Validation coverage: 0 / 8 (0.0)
- Runtime firing count: 0
- Verifier report ID: `01753ba404118a03b5d599ba1839200b80efbf8fd831a8468e84ef60a3d42e98`
- Staging/plumbing artifact only: `true`
- Human-review notes:

## Checks

- `dec007_unresolved`: true
- `human_review_notes_fields_blank`: true
- `no_final_test_access`: true
- `no_raw_rows_windows_or_plots_tracked`: true
- `no_threshold_k_prompt_rule_tuning`: true
- `official_manifest_not_used`: true
- `required_report_statement_present`: true
- `runtime_llm_free`: true
- `staging_plumbing_artifact_only`: true
- `support_scan_labels_not_used`: true
- `used_only_merged_csv`: true
- `verification_report_ids_match_task018`: true
- `verified_rule_ids_match_task018`: true

## Limitations

- This is a Kaggle/local staging run for implementation debugging only.
- It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.
- Evidence cards are aggregate human-review aids, not performance or explanation-quality claims.
- DEC-007 remains unresolved.
- No raw rows, windows, raw sequence plots, or downloadable derived samples are persisted.
