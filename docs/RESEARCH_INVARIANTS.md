# Research Invariants

These invariants govern implementation after TASK-000.

## No test leakage

Held-out test labels, intervals, outcomes, and plots must not influence candidate discovery, model training, preprocessing choices, relation profiling, calibration, rule generation, rule refinement, threshold selection, checkpoint selection, verifier tuning, or hyperparameter selection.

## GDN relations are candidates

GDN edges are candidate relations, predictive relations, or data-guided pairs. They are not causal claims, physical ground truth, or root causes.

## Runtime is LLM-free

Runtime detection and explanations execute deterministic verified DSL rules only. Runtime packages must not import LLM providers or planning modules.

## LLM output is constrained

An LLM may only use supplied candidate variables, calibrated numeric values, allowed predicates, and supplied metadata. It may not invent variables, change numbers, approve its own rule, or return executable code.

## No generated Python execution

Do not execute LLM output with `exec`, `eval`, `compile`, dynamic imports, subprocess-created Python files, or dynamic module loading. Parse structured JSON into a DSL schema and evaluate deterministically.

## Local-only SWaT governance

Raw SWaT files, real rows, windows, and screenshots containing raw sequences must not be committed or uploaded. Use `SWAT_DATA_ROOT` and synthetic fixtures in CI.

## Reproducibility

Persist schema versions, data fingerprints, config hashes, code commits, upstream revisions, seeds, split manifests, view manifests, and artifact provenance.

## Stop rather than guess

Record unresolved scientific choices in `docs/DECISIONS_REQUIRED.md`. Stop when a choice changes the scientific claim or evaluation protocol.
