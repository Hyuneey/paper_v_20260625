<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=073cac6b59ccb55f5028c6eaef8d8d9e952e42d6df500ceaf1f780e24212e814 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-010 — Separate META STAT and GDN candidate evidence

## Date

2026-08-10 (`DAY`)

## Status

`ACTIVE`

## Context

Candidate sources had different meanings and could not share one truth score.

## Alternatives Considered

- One merged rank
- GDN attention as final relation
- causal graph claim

## Decision

Use a common 144-pair universe separate arm rankings and an unscored provenance-preserving union; treat GDN as learned-graph candidate evidence only.

## Why

Candidate discovery and normal temporal confirmation are distinct evidence layers.

## Consequence

The 47-pair union feeds downstream profiling; no GDN causality or unique-benefit claim follows.

## Current Relevance

Active architecture and claim boundary.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY`

Reference: docs/task_reports/TASK-039C0_REPORT.md;docs/task_reports/TASK-039C_INTEGRATION_RECEIPT.json

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
