<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=b380205348b41f990ba655212b073ee8315d25e8e5404a91ce600b585361f7ce authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-015 — Keep runtime LLM as a conditional future comparison

## Date

2026-08-04 (`DAY`)

## Status

`CONDITIONAL`

## Context

User context says runtime LLM was left open while current authority later froze an LLM-free runtime.

## Alternatives Considered

- Activate runtime LLM now
- forbid all future comparison

## Decision

Keep the current R0 and D1 runtime LLM-free; any runtime-LLM study requires a separate design authority and must not receive prohibited outcomes.

## Why

Historical intent is not fully evidenced but current runtime authority is unambiguous.

## Consequence

No current scientific component uses a runtime LLM.

## Current Relevance

Conditional future option; not authorized or part of the present core.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `USER_CONTEXT_WITH_CURRENT_BOUNDARY`

Reference: RCC-003 task seed;docs/v6/V6_CANONICAL_ARCHITECTURE.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`MEDIUM`
