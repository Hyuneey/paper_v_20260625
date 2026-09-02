<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=bd3c29b1e277c640a8c1ee23c0f21c3fa323f8841c06180eff9ab277d13d3180 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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
