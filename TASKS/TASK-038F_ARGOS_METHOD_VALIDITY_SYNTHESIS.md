# TASK-038F: ARGOS Methodological Validity Synthesis

## Objective

Synthesize committed aggregate evidence from TASK-033 through TASK-038E into a
component-wise ARGOS methodological-validity assessment and freeze the
reference-track recommendation.

## Execution Boundary

This task is reporting-only. It may read committed Markdown and aggregate JSON
reports and calculate only direct differences or proportions already
represented by committed values.

It must not:

- call a provider or agent;
- execute detector or rule code;
- read private rules, prompts, responses, values, labels, or predictions;
- access outer data or sealed test;
- generate new scientific evidence;
- select a detector variant, branch, rule, or Aggregator winner.

## Frozen Decisions

- Overall classification:
  `partial_methodological_support`.
- Exact ARGOS reproduction: false.
- Proposed-method validation: false.
- Reference recommendation: `freeze_ARGOS_reference_track`.
- Sealed ARGOS confirmation remains optional and requires separate explicit
  approval.

## Required Evidence

The source map must bind every headline claim to a committed report, report
hash, and field path. Component judgments cover one-shot generation, Repair
operability, Repair detection utility, Review inner effectiveness, Review
outer transfer, end-to-end A3 robustness, and safety/efficiency.

## Completion

Passing status:

`passed_argos_methodological_validity_synthesis`

Passing requires zero provider, agent, runtime, outer, sealed-test, and private
artifact access, plus passing source, judgment, claim, professor-package, and
report-boundary tests.
