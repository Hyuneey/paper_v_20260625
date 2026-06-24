---
id: TASK-009
title: Implement deterministic rule verifier and structured feedback
status: blocked
depends_on: [TASK-008]
phase_gate: Milestone 4
suggested_branch: task-009-rule-verifier
---

# TASK-009: Deterministic Rule Verifier

## 1. Goal

Implement deterministic rule verification over approved normal and validation data, producing machine-readable feedback for later LLM refinement.

## 2. Architecture context

The verifier, not the LLM, is authoritative. It validates rule structure and empirical behavior without executing arbitrary code.

## 3. Verification stages

1. DSL schema validity
2. variable existence
3. metadata/type compatibility
4. calibration provenance and numeric integrity
5. sufficient normal support
6. normal false-firing measurement
7. validation event coverage measurement
8. structural duplicate detection
9. firing-overlap duplicate detection

Plausibility may initially be represented through type, metadata consistency, support, and profile consistency rather than an opaque LLM judgment.

## 4. Inputs

- candidate rule AST,
- canonical rule-view windows,
- `calibration_normal` and approved `validation` data,
- metadata,
- calibration artifacts,
- existing verified library,
- verification thresholds/config.

Final test is prohibited.

## 5. Required outputs

- verification report,
- stable feedback codes,
- measured statistics,
- pass/reject status,
- duplicate references,
- suggested action enum for refiners,
- no raw SWaT sequences in tracked report.

## 6. Required feedback example

```json
{
  "rule_id": "R-001",
  "status": "rejected",
  "issues": [
    {
      "code": "NORMAL_FP_TOO_HIGH",
      "observed": 0.082,
      "limit": 0.01,
      "suggested_action": "narrow_trigger_or_strengthen_condition"
    }
  ]
}
```

Deterministic logic must not depend on free-text feedback.

## 7. Redundancy policy

Implement:

- structural signature comparison,
- same pair/family/parameter-neighborhood comparison,
- firing Jaccard overlap,
- optional marginal validation coverage.

Thresholds must be configured and documented, not invented inside code.

## 8. Safety requirements

- Use the deterministic DSL evaluator only.
- No `exec`, `eval`, dynamic imports, subprocess execution, or generated code.
- No external API calls.
- No final test access.

## 9. Acceptance criteria

1. Every check produces structured results.
2. Calibration mutation is detected.
3. Normal false firing and validation coverage are reproducible.
4. Duplicate decisions are traceable to configured criteria.
5. No raw restricted data enters reports.
6. Test split is rejected.
7. Verifier remains usable without LLM packages.

## 10. Required tests

- valid rule pass,
- invalid schema,
- missing variable,
- type mismatch,
- missing/invalid calibration,
- high normal false firing,
- low validation coverage,
- structural duplicate,
- firing-overlap duplicate,
- deterministic report,
- malicious code payload rejection,
- test-role rejection.

## 11. Stop conditions

Stop if empirical pass thresholds or duplicate thresholds have not been approved.
