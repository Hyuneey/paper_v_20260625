<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=aec8388c69f2e3890c6995d3ea06f292ff63aff54235681b692d9a7529d29798 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-022 — MULTI_VERSION_HAI_EVALUATION_EXPANSION

## Date

2026-09-04 (`DAY`)

## Status

`ACTIVE`

## Context

The 14-unit HAI23 test1 development panel is too limited for final Recall or version-generalization claims.

## Alternatives Considered

- Keep only HAI23 test2
- artificially subdivide attack intervals
- expand to version-separated HAI panels

## Decision

Preserve test1 as DEVELOPMENT_ONLY; use HAI23 test2 as PRIMARY_HELDOUT and HAI22/21 as separate external-version replications; prohibit primary pooled Recall and require outcome-blind P1 eligibility before labels.

## Why

Version-separated panels add genuine release-level observations without turning intervals into pseudo-replicates.

## Consequence

The nominal non-development count is 146 but is not IID; each version needs its own normal-only method re-instantiation and exact numerator/denominator.

## Current Relevance

DG-05 remains mandatory before any attack data; HAIEnd is not an additional event panel; current results remain immutable.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `USER_APPROVED_VALIDATION_V2_POLICY`

Reference: research_control_center/validation_v2/evaluation_expansion/CHANGE_SUMMARY_V1.md

Source commit: `NONE`

## Confidence

`HIGH`
