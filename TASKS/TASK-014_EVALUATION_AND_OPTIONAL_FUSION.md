---
id: TASK-014
title: Run sealed evaluation protocol and optional detector fusion
status: blocked
depends_on: [TASK-013]
phase_gate: Milestone 6
suggested_branch: task-014-evaluation
---

# TASK-014: Sealed Evaluation and Optional Fusion

## 1. Goal

Implement and run a reproducible, pre-configured final evaluation for candidate discovery, rule quality, explanation output, and optional detector fusion while keeping the final test sealed until execution.

## 2. Preconditions

- Phase Gate C approved.
- Evaluation protocol and configs are frozen.
- Final test access procedure is approved.
- No pending decision changes candidate, rule, threshold, or verifier behavior.

## 3. Required comparisons

### Rule construction

- Template-only,
- One-shot LLM,
- LLM + verifier feedback.

### Runtime

- Rule only,
- Base detector only,
- Optional detector + rule fusion.

### Candidate source, if approved

- Domain-only,
- GDN,
- GDN + statistical fallback,
- optional SHAP baseline.

## 4. Metric policy

Implement only approved metrics. Initial categories:

- candidate Recall@K,
- relation-pair Recall@K,
- edge stability,
- normal rule firing rate,
- validation/test event coverage,
- rule complexity,
- affected-variable Recall@K,
- segment overlap/IoU,
- detection AUROC/AUPRC,
- PA-free point/event/range metrics.

Point adjustment is off by default. If included as supplementary:

- label it explicitly,
- document exact adjustment,
- never use it for model/rule selection.

## 5. Final-test policy

- No final-test threshold tuning.
- No final-test selection of K, windows, profiles, prompts, models, rules, or fusion weights.
- Final test execution should be one-way and logged.
- Any post-test change creates a new explicitly labeled exploratory run, not the primary result.

## 6. Optional detector fusion

Fusion must be isolated behind a clear interface. If evaluated:

- compare GDN and at least one non-GDN detector if feasible,
- tune fusion only on validation,
- report detector-only, rule-only, and fusion separately,
- keep explanation tied to fired rules rather than the fused scalar,
- record base detector provenance.

## 7. Required outputs

- frozen experiment configs,
- final-test execution log,
- machine-readable results,
- candidate-discovery report,
- rule-quality report,
- explanation report,
- optional fusion report,
- artifact/provenance index,
- at least one pre-specified case study,
- negative-result and limitation section.

Reports must not include raw redistributable SWaT sequences.

## 8. Acceptance criteria

1. Results reproduce from saved configs/artifacts.
2. Test remains unused before the final execution step.
3. Compared planners use the same approved inputs where required.
4. Runtime explanations trace to executed rules and calibration artifacts.
5. Detection and explanation quality are reported separately.
6. Failed, unsupported, and negative cases are included.
7. Data-governance audit passes.
8. Point-adjustment policy is transparent.

## 9. Required tests

- metric correctness fixtures,
- split-role guard,
- frozen-config validation,
- deterministic report generation,
- fusion interface tests if implemented,
- artifact-provenance consistency,
- no-raw-data report scan,
- final-test access audit.

## 10. Stop conditions

Stop before opening final test if any evaluation choice remains unfrozen or if the run would require test-based tuning.
