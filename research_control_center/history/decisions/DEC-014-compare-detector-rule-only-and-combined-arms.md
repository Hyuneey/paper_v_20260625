<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=073cac6b59ccb55f5028c6eaef8d8d9e952e42d6df500ceaf1f780e24212e814 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-014 — Compare Detector Rule-only and combined arms

## Date

2026-08-20 (`DAY`)

## Status

`ACTIVE`

## Context

Rule utility and detector complementarity could not be inferred from construction validity.

## Alternatives Considered

- Evaluate fusion only
- hide Rule-only inside fusion
- tune all arms together

## Decision

Execute D1 Rule-only independently and compare frozen D0 D1 and D2 artifacts under common event and episode metrics.

## Why

Rule-only visibility was needed before judging fusion and all arms required immutable comparable predictions.

## Consequence

Current pilot shows distinct D1 event responses but no supported D2 improvement; Rule-only operational utility remains unvalidated.

## Current Relevance

Active comparison architecture; stronger future validation must be newly preregistered.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `SCIENTIFIC_AUTHORITY`

Reference: docs/project_state/DECISION_LOG.md;docs/professor_feedback/ARGOS_AND_EXTENSION_MEETING_BRIEF.md

Source commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Confidence

`HIGH`
