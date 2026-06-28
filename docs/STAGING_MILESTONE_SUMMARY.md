# Staging Milestone Summary

This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.

## Scope

This document consolidates TASK-017 through TASK-020 for researcher and
professor review. It uses only existing aggregate task reports and does not run
new experiments, read raw SWaT rows, open official sealed final test data, or
resolve DEC-007.

## Milestone Summary

| Task | Result | Boundary |
|---|---|---|
| TASK-017 | Initial Kaggle/local `merged.csv` dry-run completed with zero verified rules. All 8 predeclared profiling attempts were blocked by insufficient normal support. | Staging dry-run only; no benchmark or detection claim. |
| TASK-018 | Support-aware slice selection found a predeclared staging calibration slice with 2 supported pairs and 2 verified template rules. | Slice selection ignored labels and remains staging-only. |
| TASK-019 | The 2 verified rules were reconstructed as evidence cards for `MV201 -> AIT201` and `MV201 -> AIT202`. | Human-review evidence cards only; no explanation-quality claim. |
| TASK-020 | Robustness scan reviewed 2,810 fixed-stride staging slices, found 464 passing support-aware slices, recorded 22 stability observations, and passed 2 synthetic replay cases. | Synthetic replay uses non-SWaT mini-series and validates runtime plumbing only. |

## Verified Implementation Path

- Kaggle/local `merged.csv` staging source.
- `StagingSwatMirrorManifest` only.
- Candidate universe construction.
- GDN candidate edge extraction.
- Relation profiling.
- Calibration.
- Deterministic template rule generation.
- Deterministic verification.
- Runtime evaluation.
- Evidence card audit.
- Synthetic non-SWaT violation replay.

## Claim Boundary

### Allowed Implementation Feasibility Claims

- The pipeline runs end-to-end on Kaggle/local staging data.
- The implementation path exists from staging manifest through candidate
  discovery, profiling, calibration, deterministic rule generation,
  verification, runtime execution, evidence audit, and synthetic replay.
- Runtime response-missing behavior passes synthetic sanity replay.

### Allowed Staging-Only Evidence Claims

- Support-aware slice selection resolves the initial support bottleneck for at
  least some predeclared pairs.
- Two staging verified rules were audited as evidence cards.
- TASK-020 found additional support-aware staging slices for the audited pair
  family, but those observations remain staging-only.

### Prohibited Claims

- Official SWaT benchmark performance.
- Anomaly detection performance.
- Explanation quality.
- Final physical invariant discovery.
- Thesis final result.
- Any claim that Kaggle/local staging results replace official iTrust
  evaluation.

## Risk Register

| Risk | Status | Mitigation |
|---|---|---|
| Kaggle/local source is not official iTrust. | Open | Resolve DEC-007 before final evaluation claims. |
| DEC-007 remains unresolved. | Open | Use the official iTrust route or an explicitly approved alternative before final benchmark work. |
| Metadata `review_status` remains unreviewed for relevant variables. | Open | Complete manual metadata review before final reporting. |
| Support counts are still small in audited cards. | Open | Treat cards as staging evidence until official data and broader support are available. |
| Rule IDs vary across slices due to calibration/provenance. | Observed | Report stability by pair, calibration ranges, and verifier status instead of assuming one fixed rule ID. |
| Validation runtime firing on staging data is zero. | Observed | Do not claim anomaly detection performance from staging validation. |
| Synthetic replay is non-SWaT plumbing only. | Observed | Use replay only as a deterministic runtime semantics sanity check. |

## Next Recommended Path

1. Resolve DEC-007 with official iTrust data before any final benchmark or
   thesis performance claim.
2. Alternatively, prepare a professor-facing review package that clearly marks
   all current results as staging-only before final official data access.

## Source Reports

- `docs/task_reports/TASK-017_REPORT.md`
- `docs/task_reports/TASK-017_DRY_RUN_REPORT.json`
- `docs/task_reports/TASK-018_SUPPORT_SCAN_REPORT.json`
- `docs/task_reports/TASK-018_DRY_RUN_REPORT.json`
- `docs/task_reports/TASK-019_RULE_EVIDENCE_AUDIT.json`
- `docs/task_reports/TASK-019_RULE_EVIDENCE_AUDIT.md`
- `docs/task_reports/TASK-020_RULE_ROBUSTNESS_REPORT.json`
- `docs/task_reports/TASK-020_SYNTHETIC_VIOLATION_REPLAY.json`
- `docs/task_reports/TASK-020_REPORT.md`
