# TASK-025 Completion Report

TASK-025 reconstructs the pinned ARGOS `train-LLM-only` DetectionAgentV3 prompt
path for the selected KPI series and captures a mock response for static
validation. Generated Python is not executed. No real provider is called. No
benchmark or thesis claim is made.

## Summary

- Corrected TASK-024 restricted subprocess evidence semantics so it no longer
  claims kernel-level network, repository-write, CPU, or memory isolation.
- Mapped ARGOS prompt construction to pinned files/functions.
- Resolved chunk size from pinned ARGOS defaults: `1000`.
- Selected the first deterministic train chunk containing both normal and
  anomaly labels.
- Wrote complete prompt/request, selected raw chunk, raw response, and
  quarantined rule text only under ignored `artifacts/`.
- Stored only hashes, counts, indices, and redacted metadata in tracked
  reports.
- Added provider approval template with `approved: false`.
- Captured a repository-owned mock response and statically validated the code
  fence and `inference(sample: np.ndarray) -> np.ndarray` signature.

## Prompt Fidelity Result

| Component | Result |
|---|---|
| ARGOS commit | `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` |
| Mode | `train-LLM-only` |
| System prompt source | `external/argos/agent/prompts/detection.py` |
| Template | `DETECTION_AGENT_V3_DEFAULT_PROMPT_TEMPLATE` |
| Mode selection path | `driver.py`, `runtime/engine.py` |
| Sample serialization | `DataFrame.to_string(index=False, header=False)` |
| Iteration history | first capture, no previous rule block |

## Chunk Result

| Field | Value |
|---|---|
| Selected KPI ID | `05f10d3a-239c-3bef-9bdc-a2feeb0037aa` |
| Converted CSV SHA-256 | `f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55` |
| Chunk size | 1000 |
| Start/end position | `[0, 1000)` |
| Start/end index | `0` / `999` |
| Label counts | `0`: 996, `1`: 4 |
| Chunk hash | `550f47a55f37a18337c097ae4033808ef591d75407581c2e9b3cf8da1ed42015` |
| Selection policy hash | `6e36b229e05834547771c81c9f6c763d58c8c2bda50752dac0440560bf8d3b3c` |

## Capture Result

| Field | Value |
|---|---|
| Provider mode | `mock` |
| Real provider call requested | false |
| Real provider call allowed | false |
| System prompt hash | `6e1cb2dd4997199005ced237110471d53623cbcfe89d0de83af6fdc797bfa6bc` |
| User prompt hash | `58182b3bb1c35eaf16857ef71eddbf5ba791981bf84223bb9a2e81bd51a34536` |
| Complete request hash | `14af5d91248f3ca579a445527768264f148497d58d85b49b96b39b8873918aca` |
| Raw response hash | `a39d9ae0573e686ad1281e19b6e930e8a817a8dad28f538b5854ccdaf5f0878f` |
| Rule hash | `a16fe0779e01ab7a161a64455f00d59ea118608f1478e317c6a5c170a75a06ed` |
| Code extracted | true |
| Signature valid | true |
| Static safety passed | true |
| Execution performed | false |
| Performance metric reported | false |

## TASK-024 Fallback Correction

The regenerated TASK-024 sandbox smoke report now records:

```yaml
network_isolation_enforced: false
network_observed_used: false
provider_credentials_present: false
repository_write_isolation_enforced: false
write_scope_observed: ignored_private_run_directory_only
cpu_limit_enforced: false
memory_limit_enforced: false
timeout_enforced: true
static_rule_policy_enforced: true
```

## Verification

Verification commands:

```powershell
python -m unittest tests.test_task024_argos_kpi_sandbox tests.test_task025_argos_prompt_capture -v
python -m compileall -q experiments/argos_reproduction tests/test_task024_argos_kpi_sandbox.py tests/test_task025_argos_prompt_capture.py
python -m json.tool configs/argos_reproduction/task025_prompt_capture.json
python -m json.tool docs/task_reports/TASK-025_PROMPT_CHUNK_MANIFEST.json
python -m json.tool docs/task_reports/TASK-025_PROMPT_CAPTURE_REPORT.json
git diff --check
git ls-files external dataset artifacts
git diff --name-only -- src/paperworks
```

Results:

- Targeted tests: `Ran 7 tests`, `OK`.
- Compile check: passed.
- TASK-025 config JSON validation: passed.
- TASK-025 provider approval template JSON validation: passed.
- TASK-025 chunk manifest JSON validation: passed.
- TASK-025 prompt capture report JSON validation: passed.
- `git diff --check`: passed.
- `git ls-files external dataset artifacts`: no tracked files.
- `git diff --name-only -- src/paperworks`: no changes.
- Tracked TASK-025 JSON reports do not contain raw rows, complete prompt
  messages, or generated rule text.

## Remaining Gate

Real provider calls, execution of actual generated Python, Docker/Podman
sandbox claims, full ARGOS training, RepairAgent/ReviewAgent execution, and
benchmark claims remain explicitly gated.
