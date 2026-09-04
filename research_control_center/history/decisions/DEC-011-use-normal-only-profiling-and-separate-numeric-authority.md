<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=073cac6b59ccb55f5028c6eaef8d8d9e952e42d6df500ceaf1f780e24212e814 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-011 — Use normal-only profiling and separate numeric authority

## Date

2026-08-19 (`DAY`)

## Status

`ACTIVE`

## Context

Construction evidence and numeric thresholds needed non-circular provenance.

## Alternatives Considered

- LLM-authored numbers
- label-selected construction thresholds
- anomaly-anchored evidence as core

## Decision

Profile relations and derive numeric references from authorized normal data before construction; keep evidence numeric authority and utility separate.

## Why

This prevents labels or proposed rules from defining their own acceptance values.

## Consequence

COMMON-42 runtime consumes frozen normal-derived references.

## Current Relevance

Active and central to current scientific governance.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY`

Reference: docs/task_reports/TASK-039E3_R2R_UTILITY_COMMON42_AUTHORITY_CHECK.json;docs/project_state/DECISION_LOG.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
