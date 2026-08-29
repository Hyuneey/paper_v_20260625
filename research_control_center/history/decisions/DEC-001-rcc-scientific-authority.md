<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=46e9b7f51d4a3db4a5b850c8082b2d922d5590bf543f24d56cc84e1439ed9376 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-001 — RCC scientific authority

## Date

2026-08-29 (`DAY`)

## Status

`ACTIVE`

## Context

The RCC needed one explicit scientific source of truth.

## Alternatives Considered

- Treat current checkout or thesis overlay as scientific authority

## Decision

Use origin/research-v6-thesis-checkpoint at the immutable pinned commit as RCC scientific authority.

## Why

The audited checkpoint contains the canonical scientific implementation and results.

## Consequence

All RCC scientific claims bind to the pinned authority.

## Current Relevance

Still active and foundational to every RCC view.

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `USER_APPROVED_RCC_POLICY`

Reference: research_control_center/SOURCE_AUTHORITY.md

Source commit: `e81baadcfd6cf6b9f23d307056455e024876c2ed`

## Confidence

`HIGH`
