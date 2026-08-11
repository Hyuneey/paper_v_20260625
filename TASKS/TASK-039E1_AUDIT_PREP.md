# TASK-039E1-AUDIT-PREP: Synthetic Independent Construction-Evidence Audit

## Status

`passed_task039e1_audit_preparation`

This status means only that a synthetic independent audit harness is ready.
It is not a real E1 audit result and grants no E1, E2, rule-generation, or
runtime authority.

## Objective and base

Prepare an independent verifier that can later, under separate authorization,
reconstruct and audit 42 construction-evidence records and their 462 numeric
bindings while preserving the frozen E0 cohort identity.

- Base: `20ca2e6f561ce0cdfaf822198f7b64d8e143215c`.
- Branch: `task-039e1-audit-prep`.
- The optional E1 preparation branch was not merged. The oracle is built on
  the exact E0 protocol base and does not import an E1 materializer or its hash
  helper.
- All fixtures use `SYNTHETIC_*` identities and fake numbers/hashes.

## Independent reference

The task-owned oracle independently freezes eleven roles and their origins,
canonical JSON encoding, SHA-256 numeric-reference construction, relation and
pair identity binding, source/target and direction binding, selected-horizon
binding, D1/D2 evidence hashes, source/target parameter hashes, window-bundle
hashes, public-manifest sanitization, and construction-only reference
resolution.

Numeric-reference replay changes when the numeric value, role, source
parameter hash, target parameter hash, D1 evidence hash, D2 evidence hash, or
window-bundle hash changes. Resolution also requires an exact relation binding,
numeric role, private evidence-record hash, approved evidence authority, and a
unique independently verified numeric reference.

The implementation intentionally has no project-module imports. It does not
call `materialize_construction_evidence_v1`, `stable_hash_v1`, a provider, a
rule generator, or any file reader.

## Exact future accounting

The prepared dataset audit requires:

- 42 confirmed relation primitives;
- 23 pair contexts;
- 42 private evidence records;
- 462 numeric bindings;
- exactly eleven roles per relation;
- 42 approved numeric bundles;
- 42 public manifest entries;
- zero skipped relations; and
- each frozen role occurring exactly 42 times.

The ordered E0 cohort identity-list hash is independently recomputed and must
match exactly. Duplicate relations, a mismatched partition, ten-role records,
twelve-role records, missing roles, and duplicated roles fail closed.

## Private/public boundary

Private synthetic records may carry fake source thresholds, stability
tolerances, and target scales. Public manifests carry relation identities,
directions, the public selected horizon, approved role names, evidence hashes,
the private evidence-record hash, and allowed public window protocol
constants. They reject calibrated values, raw HAI, absolute private paths, and
runtime-authority preclaims.

## Future replay design

The future replay contract names five logical inputs: D1 source parameters,
D1 target parameters, D1 directional evidence, D2 confirmations, and the E1
private construction-evidence ledger. It freezes 42/462 accounting, requires a
separate future authorization, and keeps real reads, raw HAI, and runtime
authority disabled. The current replay entry point fails before opening any
path; passing an arbitrary object as authorization does not unlock it.

## Boundary

- Real E1 result accessed: `false`.
- Real D2 result accessed: `false`.
- Real confirmed identities consumed: `false`.
- D1/D2/E1 private ledgers accessed: `false`.
- HAI accessed: `false`.
- LLM available: `false`.
- LLM called: `false`.
- Rule generation available: `false`.
- Rule generated: `false`.
- Runtime authority: `false`.
- E1 authorized: `false`.
- E2 authorization created: `false`.

No global task status or downstream authority is changed.
