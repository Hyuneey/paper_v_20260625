# Fixed-Rule Sandbox Policy

TASK-024 allows sandbox execution only for the repository-owned fixed mock rule
from TASK-023. It does not approve execution of an actual LLM-generated rule.

## Allowed Code

Allowed:

- the fixed mock rule extracted from
  `configs/argos_reproduction/task023_offline_harness.json`;
- repository-owned sandbox runner code under `experiments/argos_reproduction/`;
- the container entrypoint under `experiments/argos_reproduction/container/`.

Forbidden:

- real provider responses;
- externally supplied rule text;
- dynamically downloaded code;
- actual LLM-generated Python;
- ARGOS full training;
- detector-plus-rule combined mode.

## Sandbox Boundary

Preferred runtime order:

1. Docker;
2. Podman;
3. restricted local Python subprocess fallback.

When Docker or Podman is available, the runner uses:

- `--network none`;
- no provider credential environment variables;
- read-only rule/input mount;
- writable output directory only;
- one CPU;
- 256 MB memory limit;
- two-second timeout;
- read-only container root filesystem;
- dropped capabilities and `no-new-privileges`;
- output file-size limit;
- no main repository mount.

Container image source:

```text
experiments/argos_reproduction/container/Dockerfile
```

Image name expected by TASK-024 config:

```text
paperworks-task024-argos-sandbox:local
```

## Local TASK-024 Run

Docker and Podman were not available in the local TASK-024 environment. The
executed smoke therefore used the restricted Python subprocess fallback. The
fallback:

- runs in an ignored private run directory;
- uses `python -I`;
- passes only a sanitized environment with no provider credentials;
- performs static safety checks before execution;
- writes only a bounded output JSON;
- records hashes of input, rule, output, and sandbox config.

The fallback does not enforce kernel-level CPU or memory limits. Before any
actual LLM-generated Python can be executed, a Docker/Podman sandbox run must be
approved and verified separately.

## Smoke Result Boundary

The TASK-024 sandbox output is a plumbing diagnostic only. It validates schema,
fixed-rule invocation, output shape, binary label domain, and artifact hashing.
It is not an ARGOS benchmark and must not be used as a thesis performance
claim.
