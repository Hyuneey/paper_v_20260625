# Captured Rule Threat Model

## Protected Assets

- the main research repository and Git history;
- provider credentials and host environment variables;
- private KPI artifacts and future approved inputs;
- host network, processes, and filesystem;
- integrity of the frozen rule, container image, command, and output records.

## Threats

The captured source must be treated as untrusted even though its current hash
passes static checks. Relevant threats include unauthorized imports, unsafe
NumPy APIs, file and environment access, network or subprocess access, dynamic
attribute lookup, dunder traversal, code evaluation, top-level side effects,
path traversal, resource exhaustion, oversized output, malformed output, and
replacement of the audited rule between review and launch.

## Static Controls

- Verify the exact rule SHA-256 before every audit and future launch.
- Permit only the one observed `numpy` import.
- Freeze exact call and attribute allowlists for the fixed rule hash.
- Reject `getattr`, `setattr`, `delattr`, dunder attributes, dynamic imports,
  compilation, evaluation, file access, environment access, network access,
  subprocesses, and shell calls.
- Reject module-level behavior other than imports, literal constants, and
  function definitions.
- Keep raw source quarantined under ignored private storage.
- Track only hashes and redacted AST structures.

Static checks are necessary but not sufficient. They do not make generated
code safe to run on the host.

## Future Runtime Controls

Any future execution requires Docker or Podman, a non-root user, no network,
a read-only root filesystem, dropped capabilities, no-new-privileges, PID/CPU/
memory limits, a two-second timeout, read-only rule and input mounts, a bounded
output, bounded no-exec tmpfs, no repository mount, no host environment or
credentials, immutable image identification, command hashing, and output schema
validation.

There is no local subprocess fallback for captured rules.

## Current Residual Risk and Decision

Docker and Podman are unavailable in the current environment. The container
image was not built, its digest is unavailable, and the default execution
approval is false. Therefore:

```yaml
container_preflight_status: unavailable
captured_rule_execution_allowed: false
```

The captured rule was not executed in TASK-027.
