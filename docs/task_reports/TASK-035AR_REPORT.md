# TASK-035AR Report

## Status

`passed_balanced_generation_cohort`

TASK-035A remains immutable with status `insufficient_rule_yield`. TASK-035AR
adds an independent balanced 100-slot cohort and does not reinterpret the
original result.

## Execution

- Clean implementation commit A-R: `7933b2d`
- Provider/model: OpenAI Responses API / `gpt-5.6-luna`
- Anchors: the same frozen 50 TASK-035A anchors across 10 KPI series
- New replicate IDs: 3 and 4
- Requests: 100 one-shot calls, zero retry
- Sole generation change: `max_output_tokens` increased from 2,000 to 6,000
- Prompt bytes, chunks, provider, model, static policy, and runtime policy:
  unchanged

The preflight found the recorded `UbuntuTask033Local` distribution absent. It
was restored from the same official Ubuntu 24.04.4 WSL image after verifying
SHA-256 `9b2f7730dc68227dd04a9f3e5eab86ad85caf556b8606ad94f1f29ff5c4fd3f5`.
The same rootless Podman 4.9.3 stack and frozen image policy were rebuilt. No
rule ran before the network-none, non-root, read-only-root, CPU, memory, and PID
isolation probe passed. Docker and host rule execution were not used.

## Aggregate Results

| Stage | TASK-035A original | TASK-035AR remediation |
|---|---:|---:|
| Registered slots | 100 | 100 |
| Non-empty responses | 84 | 100 |
| Extracted rules | 61 | 100 |
| Static-valid rules | 61 | 100 |
| Runtime-executable rules | 55 | 91 |

Remediation runtime failures: 9. Provider errors, transport errors, empty
visible responses, and response-without-rule outcomes: 0.

The combined cohort contains 200 terminal slots and 146 executable rules. The
minimum cumulative count per KPI is 12, the minimum distinct-rule count per
KPI is 12, all 10 KPIs have at least 10 executable rules, and 48 of 50 anchors
have at least two executable rules.

## Gate Decision

Every frozen adequacy threshold passed. TASK-035B is authorized to start under
its own later scope and protocol. No inner selection, outer validation, test
access, detector execution, fusion execution, or anomaly-performance
calculation occurred in TASK-035AR.

These are response, extraction, runtime-contract, and balance yields only.
They are not anomaly-detection performance or benchmark results.
