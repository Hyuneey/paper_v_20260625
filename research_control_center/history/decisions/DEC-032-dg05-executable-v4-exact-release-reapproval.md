<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=b7b86c33717de93afd73c7f3a207750a86613f7353839e196ba27f96cebbab7c authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-032 — DG05_EXECUTABLE_V4_EXACT_RELEASE_REAPPROVAL

## Date

2026-09-06 (`DAY`)

## Status

`OPEN`

## Context

DEC-031 bindings normal-source lineage and one production route are frozen under a new exact V4 release;real access still requires a fresh exact user approval.

## Alternatives Considered

- Approve exact V4 release
- decline or request a new scoped closure

## Decision

USER_DECISION_REQUIRED

## Why

Historical DEC-029 and DEC-030 are suspended and cannot authorize the changed implementation bytes.

## Consequence

No attack/test/label/scenario access may occur until the exact V4 manifest and closure are explicitly approved.

## Current Relevance

CURRENT_EXACT_NEXT_DECISION

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `LOCAL_PREACCESS_CLOSURE`

Reference: research_control_center/validation_v2/dg05_v4_release/DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V4.md

Source commit: `5559d6479af33b210af8548f8cdc7b62dafbe282`

## Confidence

`HIGH`
