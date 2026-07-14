# ARGOS Rule Controllability Audit

## Control classification

| Control | Classification | Effect |
|---|---|---|
| System prompt and requested function signature | `directly_user_controllable` | Defines Python format, comments, label semantics, and broad prohibitions against hard-coded labels/indices. |
| Chunk size, split ratio, top-k, retained rule count, max iterations, timeout | `directly_user_controllable` | Changes evidence volume, search breadth, and stopping behavior. |
| Labeled train chunk | `algorithmically_controlled` | Selected from the train dictionary and serialized verbatim into the prompt. |
| Previous selected rule | `algorithmically_controlled` | Appended as `CODE FROM LAST ITERATION`; it is the explicit iteration memory. |
| Repair execution error | `algorithmically_controlled` | Triggered by direct execution failure or output shape mismatch and supplied to RepairAgent. |
| Review metric delta and code diff | `algorithmically_controlled` | Supplied when current train F1 is below previous train F1. |
| Regression samples | `algorithmically_controlled` | Up to three train windows where the previous rule was correct and the current rule is wrong. |
| Validation selector | `algorithmically_controlled` | Ranks pinned rule-only candidates by Event-F1-PA validation F1. |
| NumPy chunk sampling | `random` | Seed 8 fixes `randint` order, then chunk access uses modulo chunk count. |
| LLM completion | `provider_dependent` | Temperature 0.75, top-p 0.95, no provider seed; syntax and thresholds can vary. |
| Provider retries | `random` and `provider_dependent` | Backoff adds unseeded Python random jitter and depends on endpoint failures. |
| Internal rule thresholds and derived expressions | `implicit_or_uncontrolled` | The LLM invents or revises them; ARGOS does not bind them to an approved parameter schema. |
| Imports and computational strategy | `implicit_or_uncontrolled` | Prompt allows external libraries; extraction does not enforce an allowlist. |
| Conversation history | `implicit_or_uncontrolled` in design, effectively reset | Agents configure ten past messages but call `reset()` after responses; previous code is the reliable history channel. |

## Constraint strength

ARGOS primarily relies on prompt instructions and downstream execution/metric
feedback. It does not provide an explicit typed rule grammar, variable allowlist,
numeric-parameter registry, or deterministic verifier. RepairAgent and
ReviewAgent can rewrite Python, including thresholds and control flow.

This is the main research opportunity for the proposed multivariate method:
retain planner-repair-review mechanics while constraining outputs to a JSON DSL,
approved variable pairs, and calibration references that a deterministic engine
can validate without executing generated Python.

## Limits of controllability

- The user can control search budgets and prompts, but not the exact completion.
- Validation ranking controls which candidate survives, but the score threshold
  is itself optimized from validation labels.
- Review provides monotonicity pressure only against the previous train F1; it
  is not a proof of semantic correctness or physical validity.
- Test evaluation inside training exposes information even when it is not the
  pinned selector input.
