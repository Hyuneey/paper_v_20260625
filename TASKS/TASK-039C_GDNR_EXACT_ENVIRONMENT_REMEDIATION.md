# TASK-039C-GDNR Exact Environment Remediation

## Authority

This task performs the single bounded environment-remediation attempt approved
by independent review commit
`058b5e2023b66ccbf6704c5baf1f6c677f17b07a`. The branch starts at blocked GDN
result `c0efdb6218385ec326be1a929371242314e63cb6`. It does not authorize
TASK-039D, integration, detector work, or any change to the frozen GDN
scientific implementation.

## Immutable scientific boundary

The execution reuses, without modification:

- `src/paperworks/gdn/upstream_candidate_backend_v1.py`;
- `src/paperworks/candidates/gdn_candidate_discovery_v1.py`;
- `configs/v6/task039c_gdn_backend_v1.json`.

The architecture, raw candidate-learning view, preprocessing, learned Top-K
graph, loss, optimizer, epoch limit, early stopping, seeds, projection, and
ranking remain frozen. The existing deterministic and Torch/PyG smoke trainers
remain `synthetic_smoke_only` and are not execution fallbacks.

## Exact environment

The only permitted environment is CPython 3.12.13 on Windows AMD64 using CPU
execution and these exact top-level packages:

- `torch==2.12.1` from
  `torch-2.12.1-cp312-cp312-win_amd64.whl`, SHA-256
  `e86550597877fb272ddc52db2f85b82cb601ea7bd932576a0340152cae2200b3`;
- `torch-geometric==2.8.0` from
  `torch_geometric-2.8.0-py3-none-any.whl`, SHA-256
  `1f62e415a2e9ee69d34617d1b0b230e9d9040f51809b96e801e742770fd4dada`;
- `jsonschema[format-nongpl]==4.26.0`.

Package acquisition is a single binary-only resolution from official PyPI.
Installation is offline from the verified external wheelhouse. Source builds,
nightlies, post releases, alternate package managers, and optional PyG
extensions are prohibited.

The runner requires `TASK039C_GDN_ENV_ROOT`, `TASK039C_GDN_WHEELHOUSE`,
`TASK039C_GDN_PRIVATE_ROOT`, and `HAI_DATA_ROOT`. Every resolved root must be
distinct and outside Git. No environment path is serialized publicly.

## Execution sequence

1. Freeze Commit A and require a clean worktree at that exact commit.
2. Verify remote GDN/review lineage, zero review blockers, C0 identities,
   pinned upstream blobs, and the unchanged scientific files.
3. Rehash every wheel and write the complete private and sanitized wheelhouse
   receipts.
4. Verify imports, CPU execution, package metadata, `pip check`, the installed
   freeze, absence of optional PyG extensions, and deterministic thread/hash
   variables. Write the environment receipt outside Git before data access.
5. Consume the one-attempt marker and launch one worker from the exact
   environment.
6. Bind the full P1 header order to the frozen candidate-learning view hash,
   then load only `hai-train1.csv` and `hai-train2.csv` through the reviewed
   loader.
7. Run seeds 11, 23, and 37 sequentially with identical frozen settings. Write
   each private seed ledger outside Git. Any seed failure prevents ranking.
8. Project each learned graph onto the exact 144-pair universe, aggregate with
   denominator three, and derive top-10/20/40 as prefixes of one ranking.
9. Serialize only sanitized public receipts, the result, and the report.

## Data and result boundary

Train3, train4, test, labels, attacks, P2/P3/P4 feature values, BR2 pair-level
records, META output, and STAT output are prohibited. No model checkpoint,
state dictionary, raw window, raw time-series row, or raw node embedding may be
persisted. Attention and post-hoc XAI remain outside the primary ranking.

A passing result is graph candidate evidence only. It is not causality, a
confirmed relation, rule validity, anomaly performance, or method superiority.

## Terminal states

The attempt terminates as one of:

- `passed_task039c_gdn_candidate_discovery`;
- `blocked_exact_gdn_environment_unavailable`;
- `blocked_exact_gdn_environment_missing_unapproved_extension`;
- `failed_gdn_remediation_requires_scientific_change`;
- `failed_gdn_training`;
- `failed_gdn_data_boundary`;
- `failed_gdn_result_contract`;
- `failed_gdn_regression`.

No second dependency-remediation or real-execution attempt is permitted after a
terminal outcome.
