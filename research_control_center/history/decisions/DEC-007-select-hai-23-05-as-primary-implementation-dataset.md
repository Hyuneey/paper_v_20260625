<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=e292a040dcb35b3efff4ed02d623232f7b57003aed48ecac5716df16332272a7 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
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
