<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=b29add1b534024f6df6238e4aa2a7e24092970e16456d4d3f5aa0c2113f09294 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-020 — Adopt Formal V4 as the VALIDATION V2 Rule/runtime authority

## Date

2026-08-31 (`DAY`)

## Status

`ACTIVE`

## Context

The preferred canonical-to-V4 bridge was not selected because frozen RuleV1 and V4 semantics were non-equivalent and a forced bridge would overstate verifier authority.

## Alternatives Considered

- Migrate to canonical RuleV1/VerifierV1
- build a verified bridge
- formally adopt V4

## Decision

Use a separately versioned Formal V4 portfolio/runtime authority for VALIDATION V2, with exact relation, numeric, evaluator, config, feature, file, sampling, horizon, and execution-context replay.

## Why

Formal V4 preserves executable V4 semantics while explicitly denying canonical RuleV1 and VerifierV1 authority claims.

## Consequence

PILOT V1 remains immutable; future V2 materialized windows and predictions require their separate custody gates.

## Current Relevance

GAP-FIX-001 passed synthetic conformance and independent QA; this is not scientific execution readiness by itself.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `USER_APPROVED_VALIDATION_V2_POLICY`

Reference: research_control_center/validation_v2/reports/GAP_FIX_001_REPORT.md

Source commit: `NONE`

## Confidence

`HIGH`
