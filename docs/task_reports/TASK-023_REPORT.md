# TASK-023 Completion Report

TASK-023 resolves the source-alignment portion of DEC-027 and adds an offline, mock-only ARGOS reproduction harness. It does not approve real LLM/API calls, execution of actual LLM-generated Python, full ARGOS training, detector-plus-rule benchmarking, SWaT experiments, DEC-007 resolution, or changes to `src/paperworks`.

## Summary

- Fetched ARGOS upstream refs/tags and inspected historical README blobs.
- Confirmed current upstream HEAD equals the pinned commit
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- Confirmed no ARGOS git tags are present.
- Selected `train-LLM-only` at pinned commit `6b24161...` as the first
  rule-only reproduction target.
- Deferred combined detector-plus-rule reproduction.
- Recommended KPI Finals phase2 one-series subset as the first public
  reproduction dataset target, without downloading data in TASK-023.
- Added a provider-free offline mock harness outside `src/paperworks`.

## Outputs

- `docs/argos_reproduction/HISTORICAL_ALIGNMENT.md`
- `docs/argos_reproduction/DATASET_SELECTION.md`
- `docs/argos_reproduction/ENVIRONMENT_AND_SANDBOX.md`
- `docs/argos_reproduction/LEAKAGE_AND_METRIC_MATRIX.md`
- `experiments/argos_reproduction/README.md`
- `experiments/argos_reproduction/mock_harness.py`
- `configs/argos_reproduction/task023_offline_harness.json`
- `docs/task_reports/TASK-023_OFFLINE_HARNESS_REPORT.json`
- `docs/task_reports/TASK-023_REPORT.md`
- `TASKS/TASK-023_ARGOS_HISTORICAL_ALIGNMENT_AND_OFFLINE_HARNESS.md`

## Historical Alignment Result

| Decision item | Result |
|---|---|
| Current upstream HEAD | `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` |
| Pinned commit | `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` |
| Tags/releases | No git tags found |
| Best rule-only reproduction commit | `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` |
| Initial mode | `train-LLM-only` |
| Best detector-plus-rule candidate | `c03427f` for historical Aggregator README alignment |
| Combined status | Deferred until rule-only behavior is reproduced |
| Adapter need | Deferred; build only if pinned combined paths cannot execute reproducibly with explicit base-detector artifacts |

## Offline Harness Result

Harness report:

- Config hash: `78e16034695c180e0e89e7564e28ad4164b99891eb93e9038c0c0485e8175d84`
- Fixture hash: `b6992c25b80ce0d944f766dbb53082f5de5832cd3c77d0770da022057cc59ad5`
- Prompt hash: `f1102e53d7c1db2666566147cd86a472f8de38abb14a8125b3ad1946996fcf50`
- Mock response hash: `61b32ee7a370574b2bb1321edd664267f85b324a29e566bd105a0dfd31ff8162`
- Rule hash: `2820e2af449647e2e6aa9f9a74cf85e2cb393902525f0fa998a08be136f4bf35`

Checks:

- Provider called: false
- Network used by harness: false
- API key required: false
- Upstream ARGOS imported by harness: false
- `paperworks` imported by harness: false
- Actual LLM-generated Python executed: false
- Static safety passed: true
- Required signature valid: true

## Commands Run

```powershell
git status --short
git log -1 --oneline --decorate
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos fetch --tags --filter=blob:none origin
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos rev-parse origin/main
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos tag --list
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos log --all --date=short --pretty=format:'%h %ad %s' -- README.md
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos show c03427f:README.md
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos show c3c28af:README.md
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos show 5209273:README.md
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos show 1cfa6d3:README.md
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos log --all --date=short --pretty=format:'%H|%ad|%s' -S'train-combined-fn' -- driver.py runtime/engine.py datasets/dataset.py agent/prompts/detection.py agent/prompts/review.py
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos log --all --date=short --pretty=format:'%H|%ad|%s' -S'train-combined-fp' -- driver.py runtime/engine.py datasets/dataset.py agent/prompts/detection.py agent/prompts/review.py
git -c safe.directory=C:/Users/hyun/Desktop/paperworks/260625/external/argos -C external\argos log --all --date=short --pretty=format:'%H|%ad|%s' -S'eval-combined' -- driver.py runtime/engine.py agent/review_agent.py
Invoke-RestMethod -Uri 'https://api.github.com/repos/NetManAIOps/KPI-Anomaly-Detection/contents/Finals_dataset'
Invoke-RestMethod -Uri 'https://api.github.com/repos/NetManAIOps/KPI-Anomaly-Detection/contents/Preliminary_dataset'
<bundled-python> experiments\argos_reproduction\mock_harness.py --config configs\argos_reproduction\task023_offline_harness.json
<bundled-python> -m unittest tests.test_task023_argos_harness -v
<bundled-python> -m json.tool configs\argos_reproduction\task023_offline_harness.json
<bundled-python> -m json.tool docs\task_reports\TASK-023_OFFLINE_HARNESS_REPORT.json
git diff --check
git ls-files external
git status --short
```

## Verification Results

- Offline harness targeted tests: `Ran 2 tests`, `OK`.
- Config JSON validation: passed.
- Harness report JSON validation: passed.
- `git diff --check`: passed.
- `git ls-files external`: no tracked upstream reference files.
- `src/paperworks` unchanged.

## Remaining Gates

The next real-LLM task remains explicitly gated. Before any real reproduction
run, approve provider calls, dataset download/preprocessing, generated-Python
sandbox execution, and run artifact retention.
