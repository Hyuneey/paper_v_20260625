# ARCH-001 Data / Split Mismatches

Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

| ID | Documented behavior | Actual implementation | Type | Scientific impact | Severity | Recommended action |
|---|---|---|---|---|---|---|
| ARCH001-M01 | D1 prediction is described as frozen before label access. | The label-blind prediction object is created and self-hashed first, but its public file is written after label-derived metrics inside `_public_reports_v1`. | LABEL_ACCESS | No label-driven mutation was found, but durable replay evidence for ordering is weaker than D0/D2. | HIGH | In a new non-result-changing task, add atomic persist/reopen and an explicit state gate before D1 label access. |
| ARCH001-M02 | One generic split-governance layer appears to control all stages. | `SplitManifestV2` and `assert_operation_permitted_v2` are sound contracts, while frozen scientific bridges mostly enforce scope through separate task-specific grants and checks. | SPLIT_ROLE | Distributed enforcement increases audit and maintenance risk; no bypass was verified. | MEDIUM | Create a future conformance audit or adapter contract; do not alter frozen paths here. |
| ARCH001-M03 | train3 is often summarized only as relation confirmation. | train3 is also the frozen D0 SPE threshold calibration source. Both paths are normal-only and isolated, but share one normal split. | CALIBRATION | Acceptable within the pilot scope; creates cross-arm coupling and reduces independence of method comparison. | MEDIUM | State the dual role in all current-facing data diagrams and consider independent calibration in expanded evaluation. |
| ARCH001-M04 | test1 can look like a single untouched evaluation set. | D0/D1/D2 V1 were frozen pilot evaluations, but D2 V2 was explicitly designed after label-informed INNER diagnostics. | SPLIT_ROLE | D2 V2 is development/pilot evidence and cannot serve as independent confirmation. | HIGH | Keep V2 labeled INNER-development and use a new preregistered held-out study for confirmation. |
| ARCH001-M05 | “test2 accesses = 0” is sometimes read as no filesystem contact ever occurred. | The OUTER recovery record reports one feature-file custody access that failed before any byte read, hash, or parse. | CUSTODY | No outcome information was exposed, but coarse wording obscures the exact failure boundary. | MEDIUM | Report access attempt and zero-byte/zero-parse counters separately. |
| ARCH001-M06 | The dataset manifest marks test time-series label availability as available. | Labels are physically separate `label-test*.csv` authorities; feature CSV parsing excludes the label field. | SCHEMA | A reader could wrongly infer labels are embedded in test features. | LOW | Clarify that “available” is dataset-level paired availability, not feature-file embedding. |
| ARCH001-M07 | A single feature count can appear to describe every stage. | The source dataset has 86 points; P1 processing uses 37 features; profiling, runtime, and role-universe contracts use smaller purpose-specific subsets. | DOCUMENTATION | Count conflation can cause incorrect schema assumptions, not observed leakage. | LOW | Always name the contract with the count; do not call 12 roles or runtime subsets the full feature frame. |
| ARCH001-M08 | Split manifests can appear to be a single runtime routing authority. | BR2 freezes concatenated raw-range semantics and purge gaps, while later frozen executions commonly bind exact physical files and task-specific guards directly. | SPLIT_ROLE | Both layers are consistent in observed paths, but the adapter relationship is implicit and costly to audit. | MEDIUM | Add a future static conformance map from each task reader to its manifest role. |

## Summary

- Critical: 0
- High: 2
- Medium: 4
- Low: 2
- Verified leakage: 0

The correct conclusion is **NO VERIFIED LEAKAGE FOUND**, not “leakage is impossible.”
