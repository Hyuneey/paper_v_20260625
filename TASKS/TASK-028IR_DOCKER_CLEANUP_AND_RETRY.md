---
id: TASK-028IR
title: Bounded Docker Partial Cleanup and One Interactive Retry
status: deferred_by_researcher
depends_on: [TASK-028I]
phase_gate: ARGOS_REPRODUCTION_ENVIRONMENT_GATE
---

# TASK-028IR: Bounded Docker Partial Cleanup and One Interactive Retry

## Goal

Remove only the Docker Desktop state created by TASK-028I and perform exactly
one clean, interactive, per-user installation retry.

## Frozen decision

```yaml
decision_id: DEC-032
selected_option: bounded_docker_cleanup_and_one_retry
docker_retry_count_allowed: 1
podman_fallback_status: deferred
```

## Current result

- Pre-cleanup inventory completed before host modification.
- The signed official uninstaller was attempted once and timed out after 300
  seconds.
- The official uninstaller removed registration and most program files.
- Remaining TASK-028I and official-uninstaller paths were deletion-manifested,
  scope-verified, and removed.
- No restart is pending.
- The verified official installer is retained for the one permitted retry.
- The single interactive retry was launched with `install --user` after its
  private receipt was written.
- The official installer displayed a user-facing prompt. The task stopped for
  researcher review without accepting any agreement or changing any option.

```yaml
task_status: manual_user_action_required
docker_retry_count: 1
additional_docker_retry_allowed: false
task028_resume_allowed: false
captured_rule_execution_allowed: false
```

## Deferred decision

TASK-029 closes this environment track without another installation attempt:

```yaml
docker_installation_decision: deferred_by_researcher
deferred_until: full_experiment_execution_phase
installer_retry_consumed: true
additional_docker_retry_allowed: false
task028_resume_allowed: false
captured_rule_execution_allowed: false
```

The two installer processes started by the single retry were terminated without
relaunch. Partial per-user Docker files remain as environment debt. No further
files were deleted, and Docker/Podman was not installed or verified.

Captured rule access, research data access, provider calls, synthetic TASK-028
fixture preparation, and execution approval activation remain prohibited.
