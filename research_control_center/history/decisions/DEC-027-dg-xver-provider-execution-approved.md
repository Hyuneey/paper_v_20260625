<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=aec8388c69f2e3890c6995d3ea06f292ff63aff54235681b692d9a7529d29798 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# DEC-027 — DG_XVER_PROVIDER_EXECUTION_APPROVED

## Date

2026-09-05 (`DAY`)

## Status

`ACTIVE`

## Context

The research owner explicitly approved one normal-only external-version T2 execution for HAI22 and HAI21 under the already frozen version-bound provider contracts.

## Alternatives Considered

- Do not execute
- change model or budget
- execute the exact frozen combined contract

## Decision

APPROVED: exact gpt-5.4-mini-2026-03-17 snapshot;maximum 174 calls and 3,622,912 total tokens;USD 4.06 prospective ceiling;concurrency one;retry and fallback zero

## Why

The exact prompt, schema, evidence, privacy, custody and budget authorities were frozen and independently replayed before credential access.

## Consequence

HAI22 and HAI21 normal-only T2 heldout-candidate portfolios are frozen;DG-05 attack access remains unapproved.

## Current Relevance

DG_XVER_PROVIDER_EXECUTED_QA_PASS;MULTIPANEL_PRE_DG05_FREEZE_NEXT

## Supersedes

NONE

## Superseded By

NONE

## Evidence

Source class: `USER_APPROVED_VALIDATION_V2_POLICY`

Reference: research_control_center/validation_v2/xver_normal/provider_execution_v1/XVER_T2_PROVIDER_APPROVAL_RECEIPT_V3.json

Source commit: `NONE`

## Confidence

`HIGH`
