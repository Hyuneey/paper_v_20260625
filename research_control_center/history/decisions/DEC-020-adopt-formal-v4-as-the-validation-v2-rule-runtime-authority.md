<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=24d722f03806385e5a7b7739ad685cadcf6f9d3be9565cb0c9fdbed17de02ada authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-020 — Adopt Formal V4 as the VALIDATION V2 Rule/runtime authority

## Date

2026-08-31 (`DAY`)

## Status

`ACTIVE`

## Context

The research owner explicitly selected Option B Formal V4; the canonical-to-V4 bridge was not selected because frozen RuleV1 and V4 semantics are non-equivalent and a forced bridge would overstate verifier authority.

## Alternatives Considered

- Migrate to canonical RuleV1/VerifierV1
- build a verified bridge
- formally adopt V4

## Decision

APPROVED_FORMAL_V4: Use a separately versioned Formal V4 portfolio/runtime authority for VALIDATION V2, with exact relation, validity, replay, numeric binding, portfolio freeze, runtime authorization, config, feature, file, sampling, horizon, and execution-context controls.

## Why

Formal V4 preserves executable V4 semantics while explicitly denying canonical RuleV1 and VerifierV1 direct runtime-authority claims.

## Consequence

PILOT V1 remains immutable; the bridge is NOT_SELECTED and NOT_REQUIRED_FOR_MINIMUM_THESIS_PATH; future V2 materialized windows and predictions require their separate custody gates.

## Current Relevance

DECISION_STATE=APPROVED_FORMAL_V4; DG-01=RESOLVED_BY_USER; GAP-FIX-001 synthetic conformance and independent QA remain implementation evidence rather than scientific execution.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `USER_APPROVED_VALIDATION_V2_POLICY`

Reference: research_control_center/validation_v2/VERSION_POLICY.md

Source commit: `NONE`

## Confidence

`HIGH`
