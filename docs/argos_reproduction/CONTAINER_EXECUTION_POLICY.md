# Container Execution Policy

TASK-027 prepares, but does not approve, a container-only execution boundary
for one fixed captured-rule hash.

## Required Gate

Before a future launch, all of the following must be true:

1. A researcher-owned approval explicitly sets `approved: true` for the frozen
   rule hash and one synthetic non-KPI execution.
2. Docker or Podman is available. No other runtime is accepted.
3. The local image is built and its immutable digest is recorded.
4. The exact rule hash is verified immediately before launch.
5. The command hash and all mount paths are recorded.
6. Static import, call, attribute, and top-level policy checks still pass.

## Container Controls

- non-root image user;
- `--network none`;
- `--read-only`;
- `--cap-drop ALL`;
- `--security-opt no-new-privileges`;
- PID limit `64`;
- at most one CPU;
- memory limit `256m`;
- two-second rule timeout;
- read-only fixed rule mount;
- read-only synthetic input mount;
- writable output directory only;
- output JSON limit `65536` bytes;
- bounded `/tmp` tmpfs with `noexec` and `nosuid`;
- no main repository mount;
- no provider credentials or host environment propagation;
- output row-count, shape, and binary-domain validation.

The future runner verifies the rule hash before the direct fixed-module import.
It accepts only a payload declared as `synthetic_non_kpi`. The image and runner
were not built or run during TASK-027.

## Current Preflight

Neither Docker nor Podman was found. The preflight records an unavailable
runtime, a null image digest, a future command hash, and
`captured_rule_execution_allowed: false`.

Restricted local subprocess execution is explicitly forbidden for captured
rules. The TASK-024 fallback applies only to its repository-owned fixed mock
rule and does not carry forward.
