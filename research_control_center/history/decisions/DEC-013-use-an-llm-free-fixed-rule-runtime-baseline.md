<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=0679baf23b38ac292c9ec0334debce0277b7bbb1b7d17558ff90374c40286fe3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-013 — Use an LLM-free fixed-rule runtime baseline

## Date

2026-07 (`MONTH`)

## Status

`ACTIVE`

## Context

Evaluation needed deterministic execution separated from training-time proposal.

## Alternatives Considered

- Generated Python runtime
- LLM final runtime authority

## Decision

Execute accepted frozen rules through a deterministic LLM-free R0 runtime.

## Why

Fixed rules and traces make runtime behavior reproducible and auditable.

## Consequence

Current D1 runtime is LLM-free; alternative runtime-LLM work is only conditional under DEC-015.

## Current Relevance

Active current runtime authority.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY`

Reference: docs/v6/V6_CANONICAL_ARCHITECTURE.md;docs/RESEARCH_INVARIANTS.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
