# Repository Audit

## Repository purpose and current state

This directory currently contains a v2 Codex work-order pack for a feasibility-first research prototype:

> Graph-guided, training-time agentic verified rule construction for explainable multivariate time-series anomaly detection.

It is not yet an implementation repository. There is no `src/`, `tests/`, `configs/`, package metadata, CI workflow, or executable project code at the root. The only implementation-like code present is in read-only upstream references under `external/`.

The root was initially not a valid Git repository. After the TASK-000 repository decision, `git init` was run and the current directory is now an empty implementation repository with no commits. Raw SWaT files are ignored by `.gitignore`.

## Directory tree summary

```text
.
├── AGENTS.md
├── IMPLEMENTATION_PLAN.md
├── PACKAGE_MANIFEST.json
├── README.md
├── REVISION_NOTES.md
├── UPSTREAM_SOURCES.md
├── TASKS/
├── TEMPLATES/
├── dataset/swat/
│   ├── normal.csv
│   ├── attack.csv
│   └── merged.csv
├── external/
│   ├── argos/
│   └── gdn/
└── docs/
```

File count observed after cloning references and before writing TASK-000 docs: 29 non-upstream/work-order/data files plus upstream reference trees. The SWaT CSVs dominate disk usage.

## Development commands

No root development commands are available yet.

- Install command: not identified.
- Unit test command: not identified.
- Integration test command: not identified.
- Lint command: not identified.
- Type-check command: not identified.
- CI command: not identified.

Discovery commands run safely:

```powershell
rg --files
git status --short --branch
Get-ChildItem -Force
Get-ChildItem -Recurse -Force -Filter AGENTS.md
```

Outcome before repository initialization: root Git status was unavailable because the root was not a valid Git repository. Outcome after `git init`: `dataset/swat/*.csv` files are ignored and not tracked. No existing tests were run because there is no root test suite or package configuration.

## Existing data flow

Local SWaT-like CSV files are present in `dataset/swat/`:

- `normal.csv`
- `attack.csv`
- `merged.csv`

Metadata inspection indicates:

- all three files have the same 53-column schema,
- columns are `Timestamp`, 51 SWaT variables, and `Normal/Attack`,
- initial observed sampling interval is 1 second,
- `merged.csv` row count equals `normal.csv` rows plus `attack.csv` rows,
- `normal.csv` contains only label `Normal`,
- `attack.csv` contains only label `Attack`.

This strongly suggests `normal.csv` and `attack.csv` are label-filtered partitions of `merged.csv`, not necessarily the official SWaT normal-training file and full attack-test timeline. Per the resolved TASK-000 decisions, treat these files as `local_unverified_smoke_test` inputs only. Do not use them for final evaluation claims.

## Existing model flow

No project-native model flow exists at the root.

Reference-only model material:

- ARGOS under `external/argos` for planning/repair/review concepts.
- GDN under `external/gdn` for relation-candidate learning concepts.

Neither upstream package should be imported directly into production code unless a later task explicitly approves it.

## Test and CI coverage

No root tests, CI workflows, or test runner configuration were found.

The `external/` repositories include their own scripts and sample data, but those are upstream reference assets, not this project's validation suite. They were not executed.

## Reusable code

No project-native reusable code exists yet.

Reusable concepts only:

- ARGOS: planner/repair/review workflow, verifier feedback loop, rule ranking/selection ideas.
- GDN: sensor embeddings, embedding cosine similarity, learned Top-K graph, graph-attention forecasting.

Upstream code is not currently approved for copying or direct import.

## Conflicts with proposed architecture

1. Raw SWaT CSV files are inside the workspace. They are ignored by `.gitignore`, but moving them outside the repository and using `SWAT_DATA_ROOT` remains preferred.
2. The root Git repository has no commits yet.
3. `PACKAGE_MANIFEST.json` does not include `dataset/`, `external/`, root `UPSTREAM_SOURCES.md`, or TASK-000-generated docs.
4. The available SWaT files appear to be label-filtered derivatives; using them directly for train/calibration/test roles would risk leakage.
5. Upstream ARGOS executes generated Python code and evaluates test data in workflows; this conflicts with the local DSL/runtime rules.
6. Upstream GDN uses a legacy PyTorch/PyG stack and full-matrix Top-K behavior; this conflicts with the required modern masked `C_i` extraction.

## Recommended adapted file tree

If this directory becomes the implementation repository, create:

```text
configs/
  data/
  candidates/
  profiling/
  experiments/
docs/
  tasks/
  templates/
  ARCHITECTURE.md
  DATA_CONTRACTS.md
  DATASET_PROVENANCE.md
  UPSTREAM_SOURCES.md
  RESEARCH_INVARIANTS.md
  DECISIONS_REQUIRED.md
  EXPERIMENT_PROTOCOL.md
src/<package>/
  data/
  metadata/
  candidates/
  gdn/
  profiling/
  dsl/
  planning/
  verification/
  runtime/
  evaluation/
tests/
  unit/
  integration/
  fixtures/
scripts/
artifacts/
```

Keep `external/argos` and `external/gdn` read-only. Keep raw SWaT data outside Git-tracked paths or explicitly ignored.

## Risks and missing information

- SWaT source kind, license/terms acknowledgement, edition, and version are unverified.
- The available CSVs may not preserve official split semantics and are smoke-test-only.
- No approved split ranges exist.
- No approved canonical rule-view and optional GDN-view configs exist.
- No variable metadata source or human-review policy exists.
- No root Python package or environment strategy is approved.
- No metrics protocol is approved for final evaluation.

## Recommended next ticket

TASK-001 may start only after the user accepts the smoke-test-only dataset status. Raw SWaT files have been confirmed untracked by Git and ignored by `.gitignore`.

After Git/data placement is verified, TASK-001 can begin with dataset manifests, split-before-windowing contracts, split-role guards, and synthetic-only tests. The current local CSVs may be used only for smoke tests under `dataset_status: local_unverified_smoke_test`.
