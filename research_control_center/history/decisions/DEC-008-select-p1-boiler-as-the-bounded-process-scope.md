<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=44728c1e45e5fcf3b8f8ed8ec290b30fefff9299c838f80d7d3bfd677a1f5d16 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-008 — Select P1 Boiler as the bounded process scope

## Date

2026-08-04 (`DAY`)

## Status

`ACTIVE`

## Context

The preregistered continuous-step feasibility gate compared P1 and P3.

## Alternatives Considered

- Select both processes
- choose a process manually

## Decision

Select P1 because it alone passed the frozen normal-only feasibility gate; retain P3 as infeasible.

## Why

The result followed the preregistered gate rather than a performance outcome.

## Consequence

All current candidate relation rule and INNER evidence is P1-scoped.

## Current Relevance

Active for the current HAI MVP.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY`

Reference: docs/task_reports/TASK-039BR2_REPORT.md;c417dec4b35f900ac5a614e57716b44991a3b0e0

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
