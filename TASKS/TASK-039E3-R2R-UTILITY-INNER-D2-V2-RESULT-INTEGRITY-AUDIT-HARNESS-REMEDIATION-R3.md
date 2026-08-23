# TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R3

## Execution mode

Local audit-harness remediation plus full frozen-result integrity replay.
No D0, D1, D2 V1, or D2 V2 authoritative execution; no rule reevaluation,
result/policy/horizon/authorization mutation, test1 feature access, test2,
OUTER, remote branch, PR, or push.

## Purpose

Remediate only the R2 public Markdown provenance defect
`D2_V2_R2_AUTHORIZATION_REPORT_CHAIN_REJECTED`, preserve all three historical
blocked integrity-audit attempts, pass the corrected authority/provenance gate,
then perform one independent audit-only frozen-result oracle and stop before
V1/V2 scientific disposition.

R2 blocker artifact:
`4e6526e382dbb0bf15bae9123eeeba3a090dcb59bfd767f3b19172fe3e353c0c`.
R2 established that authorization identity is canonical artifact self-hash,
all JSON cross-bindings pass, scientific bytes/values are unchanged, and the
remaining defect is one footer-separator LF incorrectly included in the
authorization Markdown body hash.

## Repository authority

- Branch: `task-039e3-r2r-utility-inner-d2-v2-result-integrity-audit-harness-remediation-r3`.
- Base: `4bfe423dfdf8041a3100248b8dd2db84d6880796`.
- R2 A/B/C: `b14cb96a19f6474d9c10e02abbdfedf3dd7c7a73` /
  `1effce0b691b870c93e5195d930a26ec9ae92658` /
  `4bfe423dfdf8041a3100248b8dd2db84d6880796`.
- Require clean exact ancestry, no merge/rewrite/remote egress.

Read continuity and all D2 V2 design, authorization, execution, result,
original integrity-audit, R1, and R2 authorities first. Validate
`CURRENT_STATE.json` self-hash.

## Historical accounting

Historical blocked integrity-audit attempts: `3`; completed: `0`. R3 is audit
attempt `4`. On PASS total/blocked/completed becomes `4`/`3`/`1`. Scientific
V2 execution attempts/retries remain `1`/`0`; audit work is not execution.

## Frozen authorities

- Authorization identity scheme: `CANONICAL_ARTIFACT_SELF_HASH_V1`.
- Authorization artifact: `0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45`.
- Redundant `authorization_hash` in that artifact is not required and absence
  is valid.
- D2 V2 design: `ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4`.
- D0: `a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6`.
- D1: `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`.
- Source map: `f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818`.
- Native horizon: `e9825a578495396d935397e79d8c50717dccb47f069f13e93f6306f992a9407c`.
- FusionEvidenceV2: `9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb`.
- CombinedPredictionV2: `31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3`.
- MetricEvidenceV2: `3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513`.
- Result Freeze Commit: `55d41c543e110a9a6f0f5e2e2671857dba938aaa`.

## Exact Markdown body scheme

For `MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1`, inspect raw bytes only.
Require one exact BEGIN marker, one exact END marker, and the declared scheme.
Let `prefix = raw[0:marker_start]`; require `prefix.endswith(b"\n")`, then
`canonical_body = prefix[:-1]`. Remove exactly that one structural separator
LF. Never decode/re-encode, normalize newlines, trim whitespace, use
`strip`/`rstrip`, or try candidate trims until a hash matches. Unknown scheme,
missing separator, duplicate marker, and CRLF separator fail closed.

The authorization report body hash, footer Bundle-Hash and Receipt-Hash, and
the JSON authorization/readiness/bundle/receipt chain must all replay exactly
before any scientific semantic parse.

## Implementation and tests

Create only:

- this task;
- `scripts/audit_task039e3_r2r_d2_v2_result_integrity_harness_remediation_r3.py`;
- `tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r3.py`;
- `tests/test_task039e3_r2r_d2_v2_result_integrity_audit_harness_remediation_r3_independent.py`.

Test raw body boundary cases: zero/one/two body-terminal LF values plus one
separator, missing separator, duplicate BEGIN/END, unknown scheme, CRLF,
whitespace mutation, footer/bundle/receipt mutation, and over-trimming. Also
attack authorization/bindings, horizons/tokens/source collapse, prediction
closure/rows/alarms/triggers, ordering, metrics, result freeze, execution
accounting, feature/test2/OUTER/private leakage. Accepted invalid must be zero.

Commit A contains only task, harness, and both tests and is frozen before real
authority replay or scientific semantic parsing.

## One real R3 audit

After Commit A and static PASS, run one fresh R3 process. First validate Git,
historical blockers, frozen result immutability, authorization self-hash and
JSON chain, and raw-byte Markdown provenance. Only on PASS load each frozen
scientific input exactly once behind a process-local parse guard, construct one
immutable pre-label snapshot, validate private FusionEvidenceV2, prove
CombinedPredictionV2-before-label ordering, parse label once, recompute events,
episodes, six metrics, and validate private MetricEvidenceV2. Report generation
must consume only the immutable result and cannot rerun an oracle or reopen an
input.

Expected closure from frozen authorities: 42 horizons; 788 alarming D1
records/tokens; 1,335 corroboration points; triggers 1,272 recovery, 813
D0-only, 63 combined, 51,852 none; 2,148 point alarms; 54,000 ordered unique
prediction rows; 14 attack events; 143 V2 episodes, 46 D0 episodes, 98 recovery
episodes. Metrics must independently replay to the exact frozen public result.

## Reports and commits

On PASS create self-hashed R3 reports named with prefix
`TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_AUDIT_R3_` for:
AUTHORITY_IDENTITY_AUDIT, MARKDOWN_PROVENANCE_AUDIT, ROOT_CAUSE, FREEZE_AUDIT,
HORIZON_ORACLE, TOKEN_ORACLE, FUSION_ORACLE, PREDICTION_AUDIT, ORDERING_AUDIT,
EPISODE_ORACLE, METRIC_ORACLE, ACCOUNTING_AUDIT, PRIVATE_CUSTODY_AUDIT,
LEAKAGE_AUDIT, INDEPENDENT_AUDIT, READINESS, BUNDLE, RECEIPT, and REPORT.md.

The new Markdown uses the same scheme and repository writer convention; verify
writer/parser round-trip before Commit B. Commit B contains only R3 reports.
Commit C contains only six project-state updates. No push.

On PASS set D2 V2 integrity-audited and interpretation-ready true while OUTER
remains false. Status:
`passed_task039e3_r2r_utility_inner_d2_v2_result_integrity_audit_harness_remediation_r3`.
Scientific state: `D2_V2_RESULT_INTEGRITY_AUDITED`.

Exact next task after PASS:
`TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1`.

On any genuine mismatch, freeze a sanitized blocker, do not retry scientific
execution, do not modify results, do not authorize OUTER, and stop.
