<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=8fdfc6540a849c356224aa8a35e3cfda88c597be7724348872d36bb4e09a3a04 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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
