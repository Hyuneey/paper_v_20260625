# Standard Schema Registry

## Scope

TASK-032A implements structural validation only. The registry reads the seven
canonical schemas from `schemas/`; it does not copy, rewrite, or package them.
The manifest pins each schema by exact-byte SHA-256, `$id`, instance
`schema_version` constant, and TASK-030 contract commit.

Initialization fails closed when a file, digest, `$schema`, `$id`, version,
format checker, or unique registration constraint is invalid. Every canonical
schema passes `Draft202012Validator.check_schema()`. Validators are constructed
with an explicit `FormatChecker`; deprecated `RefResolver` is not used.

## Interfaces

- `load_schema_registry()` validates the manifest and schema source boundary.
- `SchemaRegistry.validate_artifact()` validates an in-memory JSON object.
- `validate_artifact()` is the default-registry convenience entry point.
- `validate_artifact_file()` reads one JSON object without modifying it.
- `StructuralValidationReport` records registry/schema/instance hashes, status,
  and deterministic normalized issues.

Issue paths use JSON Pointer notation. Issues are sorted by instance path,
schema path, validator keyword, and sanitized message. Messages never include
the rejected value, a host path, or a traceback.

## Structural Boundary

The registry owns required properties, JSON types, enumerations, constants,
patterns, array sizes and uniqueness, additional properties, date/date-time
formats, and numeric bounds. It does not resolve cross-artifact identities,
graph endpoints, variables, units across artifacts, parameter approval,
calibration provenance, evidence existence, relation semantics, or scientific
claim boundaries. Those remain future project-owned deterministic verifier
stages.

## TASK-030 Invalid Scenario Classification

| Scenario | Classification | Structural result | Semantic verifier required | Reason |
|---|---|---|---|---|
| unknown variable | semantic | valid | yes | identifier shape is valid; registry membership is external |
| unknown edge | semantic | valid | yes | edge existence requires the graph artifact |
| unsupported relation type | structural | invalid | no for this instance | frozen schema enumeration rejects the value |
| missing parameter | semantic | valid | yes | parameter ID shape is valid; registry resolution is external |
| unapproved parameter | semantic | valid | yes | approval workflow is cross-artifact policy |
| invalid unit | structural | invalid | no for this instance | unit string violates the frozen pattern |
| test-split parameter provenance | structural | invalid | no for this instance | frozen schema requires calibration split |
| executable code field | structural | invalid | no for this instance | closed object rejects the extra field |
| excessive complexity | structural | invalid | no for this instance | numeric maximum is encoded in the schema |
| explanation references nonexistent rule | semantic | valid | yes | rule existence requires another artifact |

A semantic-invalid fixture passing structural validation is expected and must
not be reported as schema-valid science or verifier acceptance.
