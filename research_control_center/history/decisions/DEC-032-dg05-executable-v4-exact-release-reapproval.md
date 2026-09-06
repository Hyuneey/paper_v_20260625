<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=2f30310500017643b70d2ae719013c78eaa5cd88f637b58d5772bd586e3d160b authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-032 — DG05_EXECUTABLE_V4_EXACT_RELEASE_REAPPROVAL

## Date

2026-09-06 (`DAY`)

## Status

`SUPERSEDED`

## Context

DEC-031 bindings normal-source lineage and one production route are frozen under a new exact V4 release;real access still requires a fresh exact user approval.

## Alternatives Considered

- Approve exact V4 release
- decline or request a new scoped closure

## Decision

USER_DECISION_NOT_GRANTED_V4_SUPERSEDED_BEFORE_APPROVAL

## Why

Historical DEC-029 and DEC-030 are suspended and cannot authorize the changed implementation bytes.

## Consequence

V4 remains historical and unapproved;it cannot authorize V10 or real access.

## Current Relevance

HISTORICAL_UNAPPROVED_V4_RELEASE

## Supersedes

NONE

## Superseded By

DEC-033

## Evidence

Source class: `LOCAL_PREACCESS_CLOSURE`

Reference: research_control_center/validation_v2/dg05_v4_release/DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V4.md

Source commit: `06ed9fbc20c6c4bd71cf734f7db254661c9a030d`

## Confidence

`HIGH`
