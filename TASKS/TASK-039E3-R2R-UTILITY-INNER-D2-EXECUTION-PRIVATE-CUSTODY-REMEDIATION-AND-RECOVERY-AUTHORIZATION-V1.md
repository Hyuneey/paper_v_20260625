# TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-PRIVATE-CUSTODY-REMEDIATION-AND-RECOVERY-AUTHORIZATION-V1

## Purpose

Remediate only the infrastructure blocker
`D2_EXECUTION_BLOCKED_PRIVATE_FUSION_EVIDENCE_WRITE_DENIED`, establish a
path-redacted writable private FusionEvidence custody plane, and issue one
explicit recovery authorization. The frozen D2 design, original authorization,
original execution implementation, D0/D1 predictions, source map, fusion
semantics, and metric semantics remain immutable.

## Absolute boundaries

This task performs no D0 or D1 prediction scientific parse, fusion computation,
CombinedPrediction generation, label parse, metric computation, D0/D1/D2
scientific execution, test1-feature access, test2 access, OUTER action, policy
change, or remote egress. The historical failed attempt remains immutable:
one infrastructure-aborted attempt, zero completed scientific executions, zero
result-driven retries, and one ephemeral private-path disclosure with zero
tracked occurrences.

## Authorized implementation

Add only a recovery custody module, a recovery authorization module, and
synthetic/static tests. The custody module may validate a separate ignored
local binding, create and preflight an approved private root using
non-scientific sentinel bytes, and provide a path-redacted atomic writer. The
authorization module may replay public hashes and issue a process-local grant
for exactly one future infrastructure recovery attempt. It may not implement
fusion.

The recovery grant freezes one additional attempt, two maximum total attempts,
one maximum completed scientific execution, and zero result-driven retries.
All design/fusion/source-map/prediction/rerun/test2/OUTER change authorities are
false.

## Commit boundaries

- Commit A: this task, the two recovery modules, and two static test files.
- Commit B: the independent adversarial test only.
- Commit C: sanitized preflight, redaction, authorization, accounting,
  readiness, bundle, receipt, and Markdown report only.
- Commit D: project continuity files only.

No push is permitted. On PASS the exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-RECOVERY-V1`.
