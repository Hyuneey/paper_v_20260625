# ARGOS Environment and Generated-Python Sandbox

TASK-023 defines the environment and sandbox boundary. It does not install ARGOS dependencies into the main `paperworks` environment and does not execute actual LLM-generated Python.

## Environment Strategy

Preferred order:

1. Docker or Podman container.
2. WSL plus isolated virtual environment.
3. Dedicated local virtual environment only if containerization is unavailable.

Recommended first implementation:

| Field | Value |
|---|---|
| Isolation | Docker/Podman container |
| Base OS | Debian/Ubuntu slim image |
| Python | 3.10, matching ARGOS README |
| Dependency source | `external/argos/requirements.txt` copied into the container build context by hash, not installed in `paperworks` |
| Dependency lock | Generate a dedicated lock under ignored experiment state before any run |
| External `diff` dependency | Required; `agent/review_agent.py` invokes command-line `diff` |
| CPU limit | 1 CPU for smoke reproduction |
| Memory limit | 2 GB for rule-only smoke; lower limits for generated-rule sandbox |
| Network | Disabled after dependency build and dataset acquisition; no network during harness or rule execution |
| Mounts | Read-only ARGOS source, read-only input fixture/dataset, writable temp output directory only |
| Credentials | No provider credentials mounted by default |

Do not install ARGOS dependencies into the main `paperworks` environment.

## Provider Credentials Policy

- TASK-023 uses `provider.name: mock`.
- API keys are not required and must not be read.
- Future real provider calls require a separate approval task.
- Prompt/response capture must default to hashes and redacted summaries.

## Generated-Python Boundary

Actual LLM-generated Python must not be executed in TASK-023.

Any future sandbox must provide:

- separate container or process;
- no write access to the main repository;
- read-only input mount;
- temporary output directory;
- no provider credentials;
- network disabled;
- CPU time limit;
- memory limit;
- output/file-size limit;
- subprocess prohibition;
- path traversal prevention;
- import allowlist;
- execution timeout;
- quarantine and hashing of generated code.

Recommended sandbox defaults:

```yaml
network: disabled
repository_mount: read_only
input_mount: read_only
output_mount: temp_only
provider_credentials: forbidden
cpu_time_limit_seconds: 2
memory_limit_mb: 256
output_file_size_limit_kb: 64
allowed_imports:
  - numpy
prohibited_calls:
  - eval
  - exec
  - compile
  - __import__
  - open
  - subprocess.*
  - os.system
timeout_seconds: 2
```

## TASK-023 Harness Behavior

`experiments/argos_reproduction/mock_harness.py`:

- reads a synthetic `value,label,index` fixture from config;
- reads a fixed repository-owned mock response;
- extracts a Python `inference(sample: np.ndarray) -> np.ndarray` function as
  text;
- hashes the prompt, response, rule, fixture, and config;
- performs static checks;
- writes a run manifest;
- stops before generated-code execution.

The mock response is fixed and repository-owned. Even so, TASK-023 does not
execute it.
