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
- `numeric_constants_with_context`: numeric values paired with redacted AST
  assignment, call, comparison, or slicing context.
- `assignments_with_redacted_expression`: assignment targets and expressions as
  structured AST data without source excerpts.
- `comparisons_with_redacted_expression`: comparison operators and operands as
  structured AST data.
- `derived_threshold_expressions`: named scale, deviation, baseline, boundary,
  and comparison-boundary expressions.
- `subscript_patterns`: redacted array base and slice structures.
- `loop_bound_sources`: loop iterators or conditions and their source names.
- `top_level_executable_statements`: module statements outside approved imports,
  literal constants, and function definitions.
- `global_state_mutations`: module mutations and `global` or `nonlocal` use.
- `dunder_attribute_access`: normalized dunder attribute references.
- `dynamic_attribute_access`: dynamic attribute operations such as `getattr`.
- `normalized_call_set`: imported aliases normalized to full module names.
- `normalized_attribute_set`: normalized attributes used by the rule.
- `execution_performed`: always `false` for TASK-026.
- `structural_diagnostics_only`: always `true` for TASK-026.

## Non-Goals

The static analysis does not validate physical correctness, anomaly-detection
performance, explanation quality, detector complementarity, or final ARGOS
reproduction quality. Captured code remains quarantined under ignored
`artifacts/` and is not executed.
