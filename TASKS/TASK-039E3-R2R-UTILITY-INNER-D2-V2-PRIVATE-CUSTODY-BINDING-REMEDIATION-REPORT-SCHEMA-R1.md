# TASK-039E3-R2R-UTILITY-INNER-D2-V2-PRIVATE-CUSTODY-BINDING-REMEDIATION-REPORT-SCHEMA-R1

## Execution mode

Local report-schema and self-hash contract remediation only.

No D0, D1, D2 V1, or D2 V2 execution; no fusion, rule reevaluation, D0
score, scientific prediction/source/horizon/CombinedPrediction parse, label
parse, metric computation, test1 feature, test2, OUTER, private evidence
copy/move/rewrite/re-persistence, frozen-result modification, or push.

## Purpose

Remediate only the report-schema blocker frozen by the prior custody-binding
remediation:

- status:
  `blocked_task039e3_r2r_utility_inner_d2_v2_private_custody_binding_remediation_r1`
- blocker: `CUSTODY_REMEDIATION_DUPLICATE_HASH_FIELD`
- blocker artifact:
  `d7b68359865cff0b8bd25ede0274fd2904729a4591d8361d17cedaf4ceb41231`

The historical invocation already established exact FusionEvidenceV2 and
MetricEvidenceV2 hashes, correct logical namespaces, outside-Git regular
non-symlink files, zero tracked copies/residue/path exposure, exact custody
module identity, and passing stable scientific/security/logical bindings.
It stopped only because a private identity payload field and the public report
self-hash field both used `artifact_hash`.

This task preserves that blocked attempt and every frozen scientific artifact,
repairs only the new report schema, creates the audit-only compatibility
receipt, freezes the completed custody finding, and stops before R5.

## Exact repository base

- Repository: `Hyuneey/paper_v_20260625`
- Branch:
  `task-039e3-r2r-utility-inner-d2-v2-private-custody-binding-remediation-report-schema-r1`
- Base: `e5d5bcb28a53177deedcb67a1285f1abaf5c791f`
- Historical remediation A:
  `7c2539332b94986f52303691347cea3557e53152`
- Historical blocker B:
  `eb650be2fd3c31d67d79811bf7ee00f232ac5a2d`
- Historical continuity C:
  `e5d5bcb28a53177deedcb67a1285f1abaf5c791f`

Require exact ancestry, clean worktree/index, no merge/rebase/history rewrite,
local-only remote state, and no push.

## Preserved accounting

- Historical blocked integrity audits: `5`
- Historical custody remediation attempts/completed: `1` / `0`
- Custody report-schema remediation attempts: `1`
- Scientific V2 attempts/retries remain: `1` / `0`
- Completed integrity audits remain: `0`

This task is neither a scientific execution nor a full integrity-audit
attempt.

## Frozen identities

- FusionEvidenceV2:
  `9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb`
- MetricEvidenceV2:
  `3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513`
- CombinedPredictionV2:
  `31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3`
- D2 V2 design:
  `ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4`
- Authorization:
  `0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45`
- Custody module:
  `c0e3faafdab0cb84e2f8e62b9380c243b0faee9ab38cc014de36fed5464d62e6`

## Frozen custody semantics

- Stable scientific/security/logical fields: `9` / `6` / `5`
- Environment-local/ephemeral/unknown fields: `5` / `4` / `0`
- R4 failed binding:
  `CANONICAL_RESOLVED_ROOT_LOCATOR / ENVIRONMENT_LOCAL_LOCATOR_ACCESS_PERMISSION`
- Absolute path equality required: `false`
- Environment-local differences only: `true`

These classifications may not be redesigned or weakened.

## Schema remediation contract

Reuse the repository canonical compact-JSON SHA-256 convention. Every new
JSON artifact has exactly one reserved `artifact_hash` self-hash, excluded
from its own hash calculation. Every referenced artifact hash uses a
role-specific `*_sha256` field.

Add a fail-closed reserved-field registry that rejects duplicate JSON keys,
dataclass alias collisions, payload/self-hash collisions, reserved
bundle/receipt collisions, unknown fields, and nested-to-flat collisions
before writing. Fixed error code:
`CUSTODY_REPORT_SCHEMA_HASH_FIELD_COLLISION`.

Do not modify or rename historical artifacts. Map the historical private
identity `artifact_hash` semantic explicitly to `fusion_evidence_sha256` or
`metric_evidence_sha256` in the new schema.

Construct one immutable
`D2V2PrivateCustodyBindingRemediationCompletionR1` from committed path-free
evidence. Rendering, bundle, and receipt construction consume only that
object and immutable report hashes. No custody validation is rerun.

## Implementation and tests

Create:

- `scripts/remediate_task039e3_r2r_d2_v2_custody_report_schema_r1.py`
- `tests/test_task039e3_r2r_d2_v2_custody_report_schema_remediation_r1.py`
- `tests/test_task039e3_r2r_d2_v2_custody_report_schema_remediation_r1_independent.py`

Tests are synthetic only and cover duplicate keys, aliases, reserved fields,
self-hash mutation, referenced-authority mutation, unknown/private/path
fields, report/bundle/receipt immutability, no validation rerun, no private
reopen, and prohibited scientific/label/feature/test2 operations. Accepted
invalid must be zero.

Commit A contains only this specification, module, and two tests. Freeze it
before report generation.

## Completion artifacts

Create new self-hashed reports with prefix:

`TASK-039E3_R2R_UTILITY_INNER_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATION_REPORT_SCHEMA_R1_`

and suffixes:

- `ROOT_CAUSE.json`
- `FIELD_CLASSIFICATION.json`
- `FUSION_EVIDENCE_IDENTITY.json`
- `METRIC_EVIDENCE_IDENTITY.json`
- `SECURITY_AUDIT.json`
- `SCHEMA_AUDIT.json`
- `COMPATIBILITY_RECEIPT.json`
- `INDEPENDENT_AUDIT.json`
- `READINESS.json`
- `BUNDLE.json`
- `RECEIPT.json`
- `REPORT.md`

Before freeze, reopen every new JSON as raw UTF-8 and verify strict duplicate
key rejection, exact canonical bytes, one `artifact_hash`, exact self-hash,
distinct role-specific references, and zero private/path material. New
Markdown uses explicit UTF-8 LF and
`MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1`.

Commit B contains only these reports. Commit C contains only the six required
`docs/project_state` updates.

## PASS state

- Status:
  `passed_task039e3_r2r_utility_inner_d2_v2_private_custody_binding_remediation_report_schema_r1`
- Custody state: `PRIVATE_CUSTODY_BINDING_COMPATIBILITY_VERIFIED`
- V2 result state: `UNCHANGED_FROZEN_INTEGRITY_AUDIT_PENDING`
- `UTILITY_INNER_D2_V2_PRIVATE_CUSTODY_BINDING_REMEDIATED = true`
- D2 V2 integrity-audited/interpretation-ready remain `false`
- OUTER remains unauthorized
- Remote remains `LOCAL_ONLY_NOT_PUSHED`

Exact next task after PASS:
`TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R5`.
Do not start it automatically.
