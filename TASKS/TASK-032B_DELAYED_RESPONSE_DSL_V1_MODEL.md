# TASK-032B: Delayed-Response DSL v1 Typed Model

## Status

Completed.

## Goal

Implement immutable typed Python records, registry-first parsing, bounded MVP
consistency checks, and deterministic canonical serialization for TASK-030
`rule_dsl` documents representing a delayed response.

## Implemented

- frozen typed records for every rule document field;
- TASK-032A structural validation before model construction;
- stable sanitized model error codes;
- one-source/one-target delayed-response MVP checks;
- fixed and interval lag checks;
- event-relative and persistence window checks;
- nested parameter-reference closure checks;
- schema-only dictionary conversion and canonical UTF-8 JSON;
- transport/document SHA-256 hashing;
- synthetic fixtures and round-trip, immutability, negative, and boundary tests.

## Authorization Boundary

Parsing is not verification or approval. Document `status` and
`verified_rule_hash` values remain untrusted until a future deterministic
verifier binds them. `runtime_authorized` is always false and is not serialized.

## Excluded

No schema modification, legacy conversion, external artifact resolution,
parameter approval, verifier expansion, runtime execution, explanation
rendering, provider call, dataset access, ARGOS execution, generated-code
execution, container action, or performance claim was performed.
