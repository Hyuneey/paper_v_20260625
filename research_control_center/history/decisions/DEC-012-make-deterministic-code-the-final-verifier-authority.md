<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=2f09c6670fd3d16b398f4d2cfedbc16f48458d9a365b3d0b2611082eb8a8254e authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-012 — Make deterministic code the final verifier authority

## Date

2026-07 (`MONTH`)

## Status

`ACTIVE`

## Context

LLM proposals required an independent admission boundary.

## Alternatives Considered

- LLM self-approval
- prompt-only checking
- no verifier

## Decision

Allow bounded proposals but require deterministic checks of structure evidence parameters split runtime and claim boundaries.

## Why

Deterministic admission is reproducible and prevents uncontrolled variables numbers or code.

## Consequence

The verifier establishes contract admissibility only; it does not prove causality performance or human usefulness.

## Current Relevance

Active and must remain distinct from scientific validation.

## Supersedes

DEC-005

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY`

Reference: docs/professor_feedback/ARGOS_FEEDBACK_RESPONSE.md;docs/v6/V6_CANONICAL_ARCHITECTURE.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
