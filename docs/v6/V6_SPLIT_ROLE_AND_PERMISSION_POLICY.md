# V6 Split Role and Permission Policy

## Roles

| Role | Authorized purpose |
|---|---|
| `normal_candidate_fit` | Candidate learner and ranker fitting |
| `normal_relation_calibration` | Normal relation profiling and deterministic parameter calibration |
| `normal_guard` | Normal false-fire and stability evaluation |
| `development` | Implementation diagnostics only |
| `inner_utility` | Label-aware revision, utility assessment, and no-op selection |
| `outer_validation` | One-way descriptive replay only |
| `sealed_evaluation` | One-time approved evaluation |

## Operation Matrix

| Operation | Only permitted role |
|---|---|
| `fit_candidate_learner` | `normal_candidate_fit` |
| `fit_candidate_ranker` | `normal_candidate_fit` |
| `profile_normal_relation` | `normal_relation_calibration` |
| `calibrate_relation_parameters` | `normal_relation_calibration` |
| `evaluate_normal_guard` | `normal_guard` |
| `run_development_diagnostic` | `development` |
| `revise_rule_with_feedback` | `inner_utility` |
| `assess_rule_utility` | `inner_utility` |
| `select_rule_or_no_op` | `inner_utility` |
| `replay_outer` | `outer_validation` |
| `run_sealed_evaluation` | `sealed_evaluation` with explicit approval |

Unknown operations fail closed. Detector-threshold selection is intentionally
not authorized because the detector policy remains unresolved.

Outer and sealed roles cannot fit, calibrate, revise, rank, select, or govern a
rule. Development cannot act as final evaluation. Inner utility cannot replace
normal relation calibration.

## Purge and Windows

The minimum purge is:

```text
window_size - 1 + maximum_required_lag
```

Raw ranges are frozen before windows. Every window is generated independently
inside one range and includes enough in-range context for the maximum required
lag. Split collections also verify the physical gap between ranges assigned to
different manifests.

## Sealed Access

A sealed split records an explicit status. A legacy adapter may produce only
`approval_required`; it cannot grant access. Runtime permission requires the
native split status to be `approved`.
