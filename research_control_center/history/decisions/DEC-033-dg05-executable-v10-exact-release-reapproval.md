<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=147db6053943fa7475df633aad0dd4d287f8e83d94aaf3ff3b80dca0b81828b0 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-033 — DG05_EXECUTABLE_V10_EXACT_RELEASE_REAPPROVAL

## Date

2026-09-06 (`DAY`)

## Status

`ACTIVE`

## Context

The controlling user explicitly approved real DG05 access under the exact immutable V10 release and its two-phase label-blind prediction-first contract.

## Alternatives Considered

- Approve exact V10 release
- decline
- request another bounded preaccess closure

## Decision

APPROVED_EXACT_DG05_EXECUTABLE_V10_FOR_DG05_REAL_ACCESS

## Why

The approval names every controlling V10 authority and does not transfer to any earlier later or modified release.

## Consequence

Real held-out feature-only prediction and the conditional one-shot scenario lease are authorized only after exact V10 replay and production initialization pass.

## Current Relevance

CONTROLLING_EXACT_DG05_V10_REAL_ACCESS_APPROVAL

## Supersedes

DEC-032

## Superseded By

NONE

## Evidence

Source class: `USER_APPROVED_VALIDATION_V2_POLICY`

Reference: research_control_center/validation_v2/dg05_v10_real_execution/DG05_V10_USER_APPROVAL_RECEIPT_V1.json

Source commit: `NONE`

## Confidence

`HIGH`
