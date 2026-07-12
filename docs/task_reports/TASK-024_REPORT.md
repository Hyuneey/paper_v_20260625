# TASK-024 Completion Report

TASK-024 prepares one public KPI series for ARGOS rule-only reproduction and
executes only the repository-owned fixed mock rule from TASK-023. It does not
call a real LLM provider, does not execute actual LLM-generated Python, does
not run full ARGOS training, and does not make benchmark or thesis claims.

## Summary

- Downloaded approved KPI packages into ignored `artifacts/` paths.
- Recorded source repository commit, package URLs, Git blob SHAs, local
  SHA-256 hashes, byte sizes, extraction timestamp, and extracted file hashes.
- Confirmed the pinned ARGOS preprocessing script reference
  `utility/generate_csv.py` was not found in inspected history.
- Added a minimal KPI-to-ARGOS adapter under `experiments/argos_reproduction/`.
- Selected exactly one KPI ID using the predeclared lexicographic eligibility
  rule.
- Converted the selected series to `value,label,index` under ignored
  `artifacts/`.
- Added Docker/Podman sandbox support files and a restricted subprocess
  fallback.
- Ran the fixed TASK-023 mock rule smoke with no provider call and no actual
  LLM-generated Python execution.

## Outputs

- `docs/argos_reproduction/KPI_DATASET_MANIFEST.md`
- `docs/argos_reproduction/KPI_PREPROCESSING_PROTOCOL.md`
- `docs/argos_reproduction/FIXED_RULE_SANDBOX_POLICY.md`
- `experiments/argos_reproduction/kpi_prepare.py`
- `experiments/argos_reproduction/sandbox_runner.py`
- `experiments/argos_reproduction/container/Dockerfile`
- `experiments/argos_reproduction/container/run_fixed_rule.py`
- `configs/argos_reproduction/task024_kpi_sandbox_smoke.json`
- `docs/task_reports/TASK-024_KPI_DATASET_MANIFEST.json`
- `docs/task_reports/TASK-024_SANDBOX_SMOKE_REPORT.json`
- `tests/test_task024_argos_kpi_sandbox.py`
- `TASKS/TASK-024_KPI_DATASET_AND_SANDBOX_SMOKE.md`

## Dataset Result

| Field | Value |
|---|---|
| Source repository commit | `d06bda15d511d930cbf4e6a6de14bd94d790f0f2` |
| Train package SHA-256 | `5611dec5c912353427ac28f6c6481126a485b1229d0ca9692dc3462aa9116081` |
| Ground-truth package SHA-256 | `308b0e58555ccdc71d852aa53d15be8f24d415fef599136763e3df3849e29bd2` |
| Selected KPI ID | `05f10d3a-239c-3bef-9bdc-a2feeb0037aa` |
| Selected row count | 146255 |
| Selected label counts | `0`: 144970, `1`: 1285 |
| Converted CSV SHA-256 | `f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55` |
| Dataset manifest hash | `6fd47e3c7ed27793c5a71a0c474a6deb01d38f69cf5254a0ff79b68df708fc7c` |

The converted CSV is private and ignored by Git.

## Sandbox Smoke Result

| Field | Value |
|---|---|
| Fixed rule hash | `2820e2af449647e2e6aa9f9a74cf85e2cb393902525f0fa998a08be136f4bf35` |
| Sandbox config hash | `b27b1017d85e47fdd807c897151f92e0cae3a13e10989a98d74c23d79140976c` |
| Input slice hash | `428548f89ba886aa71e317e04ec830e8e0ff088c8e94dd3e8d5a4a73353e6e23` |
| Output hash | `8103b40219aafadd947779b4fa013b7f674c3ea683e1f623ee9e1b30282624f4` |
| Exit code | 0 |
| Input rows | 512 |
| Output label count | 512 |
| Output domain | binary |
| Output shape check | passed |

Docker/Podman were unavailable in the local environment, so the executed smoke
used the restricted Python subprocess fallback. TASK-025 corrected the evidence
semantics: this fallback is not a secure sandbox and does not enforce
kernel-level network isolation, repository-write isolation, CPU limits, or
memory limits. It only records that no network use was observed, no provider
credentials were present, writes stayed in the ignored private run directory,
the timeout was enforced, and static fixed-rule policy checks ran. Actual
LLM-generated Python execution remains gated until a Docker/Podman sandbox run
is approved and verified.

## Boundary Checks

- Real provider calls: false.
- API key use: false.
- Actual LLM-generated Python execution: false.
- Full ARGOS training: false.
- Combined detector-plus-rule path: false.
- SWaT access: false.
- `src/paperworks` changes required: false.
- Benchmark claims: false.
- Thesis claims: false.

## Commands Run

```powershell
<bundled-python> experiments\argos_reproduction\kpi_prepare.py --config configs\argos_reproduction\task024_kpi_sandbox_smoke.json
<bundled-python> experiments\argos_reproduction\sandbox_runner.py --config configs\argos_reproduction\task024_kpi_sandbox_smoke.json
<bundled-python> -m unittest tests.test_task024_argos_kpi_sandbox -v
<bundled-python> -m json.tool configs\argos_reproduction\task024_kpi_sandbox_smoke.json
<bundled-python> -m json.tool docs\task_reports\TASK-024_KPI_DATASET_MANIFEST.json
<bundled-python> -m json.tool docs\task_reports\TASK-024_SANDBOX_SMOKE_REPORT.json
<bundled-python> -m compileall -q experiments\argos_reproduction tests\test_task024_argos_kpi_sandbox.py
git diff --check
git ls-files external dataset artifacts
git diff --name-only -- src\paperworks
$env:PYTHONPATH='src'; <bundled-python> -m unittest -v
```

## Verification Results

- TASK-024 targeted tests: `Ran 3 tests`, `OK`.
- JSON validation passed for the TASK-024 config, KPI manifest, and sandbox
  smoke report.
- Compile check passed for `experiments/argos_reproduction` and the TASK-024
  test file.
- `git diff --check`: passed.
- `git ls-files external dataset artifacts`: no tracked files.
- `git diff --name-only -- src\paperworks`: no changes.
- Full unittest without `PYTHONPATH=src` failed because the `src/` layout was
  not on the import path.
- Full unittest with `PYTHONPATH=src` ran 135 tests; 127 passed and 8 import
  errors remained because the current bundled Python lacks `torch`. The failing
  tests are pre-existing GDN/task smoke imports that require the PyTorch stack,
  not TASK-024 code paths.

## Remaining Gate

The next real-LLM reproduction step remains explicitly gated. Before executing
actual LLM-generated Python, approve and verify a Docker/Podman sandbox with
network disabled, credentials absent, and resource limits enforced.
