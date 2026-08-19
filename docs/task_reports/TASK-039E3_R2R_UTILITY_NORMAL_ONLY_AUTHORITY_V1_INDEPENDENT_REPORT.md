# TASK-039E3 R2R Utility Normal-Only Authority V1 Independent Audit

## Decision

Status: `blocked_task039e3_r2r_utility_normal_only_authority_v1_independent_audit`

The scientific calibration and committed COMMON-42 identity checks passed, but six fail-closed authority/custody criteria did not. Real normal-only materialization is therefore not ready. No implementation repair was made in this audit.

## What passed

- Route-C claim boundary remained exact: this is a new normal-only authority and does not restore historical E1 or numeric-registry identity.
- COMMON was independently reconstructed as 42 accepted relations and zero `no_rule`; all 42 relation identities and semantic hashes matched.
- Historical numeric custody was independently explained as 42 relations × 11 roles = 462 bindings.
- The utility registry uses exactly ten roles and 420 bindings. The only excluded role is `selected_delay_horizon_seconds`, which remains frozen in each executable signature and semantic hash.
- Both frozen calibration source files matched their expected Git blobs and raw-byte hashes.
- Independent source-threshold, stability-tolerance, target-scale, two-file boundary, and frozen-window oracles matched the implementation.
- The expected train1/train2 identities matched the original committed dataset manifest and D1 data-access audit. Train3, test files, and labels remained excluded.
- The loader verifies both files before either scientific parser and re-verifies both after parsing. Synthetic post-read mutation was rejected.
- The canonical registry contains 420 records, 420 logical keys, and 420 unique new references. Canonical record mutations and historical-identity collision mutations were rejected.
- Canonical atomic finalization writes the private registry, validates the locator, re-hashes the private registry, and writes the public receipt last.
- T2 utility scope remains unauthorized.

## Blocking findings

1. `BLOCKER_NORMAL_ONLY_AUTHORITY_V1_COMMON_RELATION_AUTHORITY_REPLAY_BYPASS`

   Low-level registry, receipt, and finalization validators trust a caller-created authority object. They do not independently replay it against committed COMMON artifacts or recompute its definition hash. A fabricated relation identity/horizon can therefore validate while retaining canonical public hashes.

2. `BLOCKER_NORMAL_ONLY_AUTHORITY_V1_PRIVATE_LOCATOR_PRECHECK_AFTER_VALUE_PARSE`

   The canonical materializer validates the private locator and destination only during finalization, after both normal files have been parsed and calibration has run. This violates the frozen pre-read authority-gate order.

3. `BLOCKER_NORMAL_ONLY_AUTHORITY_V1_BUILDER_COMMIT_CALLER_AUTHORITY`

   The future builder commit is caller supplied. The checkout validator accepts any clean HEAD when the caller supplies the same commit, rather than internally requiring `d58757b63d21519bc39398ddcf96be1682e8b01a`.

4. `BLOCKER_NORMAL_ONLY_AUTHORITY_V1_PUBLIC_RECEIPT_OPEN_SCHEMA_LEAKAGE`

   Receipt validation uses forbidden-key and absolute-path heuristics rather than an exact closed schema. A self-rehashed additional numeric field under an innocuous key was accepted.

5. `BLOCKER_NORMAL_ONLY_AUTHORITY_V1_FINAL_LOCATOR_PATH_NOT_REVALIDATED`

   Final validation checks the private path stored inside the locator but does not require the locator-manifest file itself to remain outside Git.

6. `BLOCKER_NORMAL_ONLY_AUTHORITY_V1_LOCATOR_RECEIPT_BUILDER_COMMIT_NOT_CROSS_BOUND`

   Final validation does not require the locator and public receipt to bind the same builder commit.

## Test evidence

- Independent audit tests: 28 total, 22 passed, 6 failed as blocker evidence.
- Existing implementation synthetic tests: 24/24 passed as supplementary regression only.
- `compileall`: passed.
- `pip check`: no broken requirements.
- Frozen/upstream JSON self-hashes: 10/10 passed before report creation.
- Production source and the existing V1 test file were unchanged from the audited base.

## Boundaries and readiness

- HAI normal values accessed: 0
- HAI test values accessed: 0
- HAI labels accessed: 0
- Utility computations: 0
- Provider calls: 0
- API-key access: false
- Scientific LLM calls: 0
- Real authority materialized: false

`NORMAL_ONLY_AUTHORITY_PROTOCOL_AUDITED = false`

`NORMAL_ONLY_AUTHORITY_REAL_MATERIALIZATION_READY = false`

`NORMAL_ONLY_AUTHORITY_MATERIALIZED = false`

`UTILITY_EVALUATOR_IMPLEMENTATION_READY = false`

`UTILITY_EXECUTION_AUTHORIZATION_READY = false`

Exact next task: `NONE_AUTOMATIC`. Per the audit stop rule, the failed implementation is not repaired in this task and no automatic remediation begins.
