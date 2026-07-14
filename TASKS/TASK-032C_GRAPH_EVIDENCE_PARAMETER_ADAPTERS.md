# TASK-032C: Typed External Artifacts and Phase 1 Adapters

## Status

Completed.

## Implemented

- canonical self-hashing that excludes only top-level `artifact_hash`;
- immutable typed graph, evidence-package, and calibration-parameter models;
- TASK-032A registry-first parsing and bounded document-integrity checks;
- explicit mapping-based Phase 1 graph, evidence, and parameter adapters;
- fail-closed `created`, `pending_context`, `unsupported_source`, and
  `invalid_source` results;
- immutable non-authoritative delayed-response artifact collection;
- synthetic contract/source fixtures and focused regression tests.

## Boundary

Adapter source hashes and target hashes provide provenance and integrity only.
No rule is bound, approved, verified, or executed. No raw events or sequences,
dataset access, provider call, ARGOS action, generated Python, optional GDN
import, or runtime behavior is involved.
