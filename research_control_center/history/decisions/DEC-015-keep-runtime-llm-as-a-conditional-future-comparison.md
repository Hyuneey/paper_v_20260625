<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=531715147a805705e6bee5c8227139ac6ab613dab0be18a83f7552d1efb368f3 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-015 — Keep runtime LLM as a conditional future comparison

## Date

2026-08-04 (`DAY`)

## Status

`CONDITIONAL`

## Context

The research owner confirms runtime LLM was left open while current authority froze an LLM-free runtime.

## Alternatives Considered

- Activate runtime LLM now
- forbid all future comparison

## Decision

Keep current R0 and D1 runtime LLM-free; any runtime-LLM study requires separate design authority and cannot receive prohibited outcomes.

## Why

The historical option is user-confirmed and the current runtime prohibition is source-backed.

## Consequence

No current scientific component uses a runtime LLM.

## Current Relevance

Conditional future option; not authorized or part of the present core.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `USER_CONFIRMED_CONTEXT_WITH_CURRENT_BOUNDARY`

Reference: ARCH-000 confirmation 4;docs/v6/V6_CANONICAL_ARCHITECTURE.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`MEDIUM`
