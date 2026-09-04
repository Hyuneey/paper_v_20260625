<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=073cac6b59ccb55f5028c6eaef8d8d9e952e42d6df500ceaf1f780e24212e814 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-007 — Select HAI 23.05 as primary implementation dataset

## Date

2026-08-02 (`DAY`)

## Status

`ACTIVE`

## Context

A provenance-verified multivariate CPS dataset was required for the bounded MVP.

## Alternatives Considered

- Continue SWaT staging
- use unverified payload routes

## Decision

Use the exact provenance-audited HAI 23.05 edition under restricted local custody.

## Why

The approved source and byte-equivalence audits established a controlled dataset authority.

## Consequence

Current P1 architecture and pilot evidence bind to HAI 23.05; SWaT and WADI remain future validation candidates.

## Current Relevance

Active for the current MVP only.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY`

Reference: docs/task_reports/TASK-039A_REPORT.md;docs/task_reports/TASK-039AR_REPORT.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
