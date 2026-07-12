# ARGOS Offline Reproduction Harness

This directory is outside `src/paperworks` and is reserved for ARGOS
reproduction experiments.

TASK-023 scope:

- mock-only;
- provider-free;
- no API keys;
- no real ARGOS benchmark;
- no upstream ARGOS import into production runtime;
- no execution of actual LLM-generated Python.

The initial harness reads
`configs/argos_reproduction/task023_offline_harness.json`, extracts a fixed
mock ARGOS-style Python rule from a recorded response, hashes the prompt,
response, rule, fixture, and config, performs static checks, and writes
`docs/task_reports/TASK-023_OFFLINE_HARNESS_REPORT.json`.

Run:

```powershell
<bundled-python> experiments\argos_reproduction\mock_harness.py --config configs\argos_reproduction\task023_offline_harness.json
```

The harness stops before generated-code execution. Any future execution of
actual LLM-generated Python requires a separately approved sandbox task.
