<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=7843bc595fd526de37fa6765d7982848c00d23c6391d954f25e1ba155557c3ea authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-009 — Use pairwise temporal relations first

## Date

2026-08 (`MONTH`)

## Status

`ACTIVE`

## Context

The first HAI method needed an auditable relation unit and the original discrete-source family was infeasible.

## Alternatives Considered

- Multi-stage tree or hierarchy rules first
- weaken discrete feasibility criteria

## Decision

Use pairwise continuous-step delayed-response relations for the first MVP and keep complex relation families conditional.

## Why

Pairwise relations are bounded enough to profile bind verify execute and compare without unsupported complex-dynamics claims.

## Consequence

The current rule family is pairwise; complex hierarchy and feedback-loop work is deferred rather than disproven.

## Current Relevance

Active pairwise scope with conditional future expansion.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY_WITH_USER_CONTEXT`

Reference: docs/v6/V6_CANONICAL_ARCHITECTURE.md;docs/task_reports/TASK-039BR1_REPORT.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
