<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=c0e0ce97206de8f04c9cd4ccd865cb3ea586816aea0bf8e6736264658eef9b89 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-020 — Choose final scientific Rule/runtime authority

## Date

2026-08-29 (`DAY`)

## Status

`OPEN`

## Context

The frozen pilot executed the V4 COMMON-42 authority plane while canonical RuleV1 and VerifierV1 are adjacent contracts rather than the proven direct runtime authority.

## Alternatives Considered

- Migrate to canonical RuleV1/VerifierV1
- formally adopt V4
- build a verified bridge

## Decision

Research owner must choose the final validation authority after reviewing GAP-000 and ARCH-011 evidence.

## Why

The choice changes future contract scope and methodology wording and cannot be made for architectural elegance alone.

## Consequence

Blocks expanded D1/D2 and held-out validation but does not invalidate the frozen V4 pilot.

## Current Relevance

Open research-owner decision before expanded validation.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `GAP_000_TRIAGE`

Reference: research_control_center/architecture/gap_000_pre_validation/GAP_000_USER_DECISIONS_REQUIRED.md

Source commit: `NONE`

## Confidence

`HIGH`
