<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=d8621bd8db303ebab5ecb0cc0b0e105690c09387cfa737ccb9ecd6b7cd60fa79 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-017 — Classify current INNER results as pilot-only

## Date

2026-08-23 (`DAY`)

## Status

`ACTIVE`

## Context

The frozen comparison uses 14 contiguous attack-event units whose statistical independence is not established and a simple PCA-SPE baseline.

## Alternatives Considered

- Call the results validated performance
- discard the observations

## Decision

Report exact frozen observations while prohibiting broad performance generalization or operational claims.

## Why

Integrity-audited arithmetic does not supply sample breadth independence baseline strength or held-out confirmation.

## Consequence

Current D0 D1 and D2 numbers remain useful pilot evidence and nothing stronger.

## Current Relevance

Active claim and reporting boundary; current wording corrects the former independent-event shorthand without rewriting historical reports.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY`

Reference: docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V1_V2_DISPOSITION_V1_REPORT.md;docs/professor_first_results_v1/07_CLAIM_MATRIX.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
