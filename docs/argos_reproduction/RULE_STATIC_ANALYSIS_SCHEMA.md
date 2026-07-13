# TASK-026 Rule Static Analysis Schema

The TASK-026 static analysis report is structural only. It is not a
rule-quality metric, anomaly-detection metric, benchmark result, or thesis
claim.

## Report Fields

- `code_fence_count`: number of markdown code fences in the captured response.
- `code_extraction_status`: extraction result for the first Python code fence.
- `source_code_line_count`: line count of extracted code.
- `inference_definition_count`: number of functions named `inference`.
- `syntax_parse_status`: Python AST parse status.
- `syntax_error`: parse error string when parsing fails.
- `required_signature_status`: status for
  `inference(sample: np.ndarray) -> np.ndarray`.
- `signature`: parsed signature details if available.
- `static_safety_passed`: import/prohibited-call check result.
- `imported_modules`: top-level imported modules.
- `prohibited_calls`: prohibited direct or attribute calls detected by AST.
- `function_calls`: function call names observed by AST.
- `condition_count`: number of `if`, `while`, boolean operation, and comparison
  nodes.
- `numeric_constant_count`: number of numeric constants in the AST.
- `comparison_operators_used`: comparison operator names observed.
- `threshold_like_numeric_constants`: numeric constants excluding common
  structural values `0`, `1`, and `-1`.
- `normal_rule_comments_exist`: whether comments mention normal rules.
- `abnormal_rule_comments_exist`: whether comments mention abnormal rules.
- `indices_or_labels_hardcoded_suspected`: coarse flag for possible hard-coded
  index or label use.
- `index_keyword_present`: whether source text includes `index` or `indices`.
- `label_keyword_present`: whether source text includes `label` or `labels`.
- `suspicious_index_constants`: integer constants that may indicate index
  hard-coding.
- `suspicious_label_constants`: binary constants observed while label keywords
  are present.
- `estimated_cyclomatic_complexity`: simple branch-count estimate.
- `execution_performed`: always `false` for TASK-026.
- `structural_diagnostics_only`: always `true` for TASK-026.

## Non-Goals

The static analysis does not validate physical correctness, anomaly-detection
performance, explanation quality, detector complementarity, or final ARGOS
reproduction quality. Captured code remains quarantined under ignored
`artifacts/` and is not executed.
