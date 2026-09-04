<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=e46d8693784d1b02603c10764c3a14f9a8ee34266d00953472cfa581a1c90937 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-021 — Approve conditional Graph-Guided and Agentic contribution policy

## Date

2026-08-29 (`DAY`)

## Status

`ACTIVE`

## Context

Current evidence implements both capabilities but does not validate stable GDN contribution or verifier-feedback benefit.

## Alternatives Considered

- Retain both labels unconditionally
- remove both immediately
- make retention conditional on EXP-01 and EXP-03 evidence

## Decision

Retain Graph-Guided and Agentic as contributions only when EXP-01 and EXP-03 respectively support them.

## Why

This avoids post-hoc title expansion while preserving a feasible minimum thesis if either contribution is unsupported.

## Consequence

The verified relational rule-construction core remains viable if either conditional contribution is not supported.

## Current Relevance

User-approved policy recorded by ARCH-011; contribution status remains conditional on future evidence.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `GAP_000_TRIAGE`

Reference: research_control_center/architecture/11_outer_reproducibility/ARCH_011_VALIDATION_V2_VERSIONING.md

Source commit: `NONE`

## Confidence

`HIGH`
