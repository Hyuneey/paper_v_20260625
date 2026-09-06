<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=2f30310500017643b70d2ae719013c78eaa5cd88f637b58d5772bd586e3d160b authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-031 — DG05_PRODUCTION_CHAIN_SCENARIO_TIME_RUNTIME_AND_NORMAL_SOURCE_BINDING

## Date

2026-09-06 (`DAY`)

## Status

`ACTIVE`

## Context

The preserved PRE-DG05 audit found plural-delay duplicate/gap runtime-census and normal-source-lineage blockers.

## Alternatives Considered

- Keep historical V3 assumptions
- apply the exact approved fail-closed bindings and scoped source materialization

## Decision

APPROVED_WITH_FAIL_CLOSED_TIME_AXIS_AND_SCOPED_NORMAL_SOURCE_MATERIALIZATION

## Why

The approved choices remove semantic ambiguity while preserving fail-closed physical-time and source-lineage requirements.

## Consequence

Real DG05 access remains NO_GO;binding and normal-only source closure proceed prospectively under a new executable release.

## Current Relevance

DG05_DEC031_BINDINGS_AND_NORMAL_SOURCE_CLOSED

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `USER_APPROVED_VALIDATION_V2_POLICY`

Reference: research_control_center/validation_v2/dg05_dec031_binding/DEC031_BINDING_AUTHORITY_V1.json

Source commit: `NONE`

## Confidence

`HIGH`
