# Codex Work-Order Pack v2

This package contains revised implementation instructions for:

> **Graph-guided, training-time agentic verified rule construction for explainable multivariate time-series anomaly detection.**

## What changed in v2

This revision incorporates the actual upstream repositories and SWaT constraints:

- ARGOS is used as an architectural reference, not as the SWaT data/runtime layer.
- LLM-generated Python execution is prohibited.
- GDN is treated as a modernized, masked candidate-relation learner.
- Candidate Top-K must be computed inside `C_i`, with candidate self-edges excluded.
- Upstream GDN test-tuned evaluation logic is not reused.
- SWaT remains local-only and is never committed or uploaded through GitHub.
- A canonical high-resolution rule view is separated from an optional GDN view.
- Raw timelines are split before window generation, with purge gaps.
- Point adjustment is disabled by default.

## Files

- `AGENTS.md` — repository-wide scientific, data, safety, and coding rules.
- `IMPLEMENTATION_PLAN.md` — phases, dependencies, gates, and definitions of done.
- `TASKS/TASK-000...TASK-014` — narrow work tickets.
- `TASKS/TASK_TEMPLATE.md` — future-ticket template.
- `TEMPLATES/UPSTREAM_SOURCES_TEMPLATE.md` — upstream pinning and reuse register.
- `TEMPLATES/DATASET_MANIFEST_TEMPLATE.md` — local SWaT provenance template.
- `TEMPLATES/THIRD_PARTY_NOTICES_TEMPLATE.md` — license-notice template.
- `TEMPLATES/DECISIONS_REQUIRED_TEMPLATE.md` — unresolved-decision template.

## GitHub placement

Recommended placement in the implementation repository:

```text
AGENTS.md
IMPLEMENTATION_PLAN.md
docs/tasks/*.md
docs/templates/*.md
```

Do not place SWaT raw data, real rows, windows, or screenshots containing raw sequences in the repository.

## Local data setup

Use an environment variable:

```bash
export SWAT_DATA_ROOT=/absolute/local/path/to/swat
```

The project must validate local files and create a manifest. It must not auto-download SWaT in CI or copy it into the repository.

## Recommended GitHub workflow

1. Run one ticket per branch and pull request.
2. Use the ticket ID in branch and PR title.
3. Include the ticket's final report in the PR description.
4. Do not begin a ticket until dependencies and phase gates pass.
5. Bring PR links, diffs, logs, and aggregate artifacts back for review.
6. Use synthetic fixtures in CI.

## Execution order

```text
TASK-000  Repository/upstream/dataset audit
TASK-001  Data manifests, views, leakage-safe splits
TASK-002  Variable metadata schema
TASK-003  Candidate Universe Builder
TASK-004  Modern masked GDN candidate extraction
TASK-005  Candidate feasibility kill-test
TASK-006  High-resolution relation profiling/calibration
TASK-007  Safe JSON/AST DSL and schema registry
TASK-008  Template rule builder
TASK-009  Deterministic verifier
TASK-010  Runtime rule engine
TASK-011  Validation-only end-to-end deterministic feasibility
TASK-012  Provider-neutral LLM rule planner
TASK-013  Verifier-feedback rule refiner loop
TASK-014  Sealed evaluation and optional fusion
```

The first command to Codex should use `TASK-000`.

## Current specification milestone

TASK-030 defines the implementation contract for the ARGOS-informed
multivariate CPS extension. The milestone includes versioned graph, evidence,
rule DSL, parameter, verifier, runtime, and explanation schemas with synthetic
validation fixtures.

This is a **specification milestone only**. It does not mean that the complete
method, LLM planner, deterministic calibrators, verifier, runtime interpreter,
detector fusion, or official SWaT experiment has been implemented or
experimentally verified. See
`docs/method/GRAPH_GUIDED_RULE_CONSTRUCTION_CONTRACT.md`.

## Current migration-planning milestone

TASK-031 maps the existing Phase 1 deterministic implementation to the frozen
TASK-030 contracts and freezes a delayed-response-only MVP migration path. It
also separates standard JSON Schema validation from project-owned semantic
verification and requires explicit, hash-recorded legacy adapters.

This is a **migration-planning milestone only**. No TASK-030 production method
code, dependency, dataset experiment, provider integration, generated-code
execution, or performance result was added. See
`docs/method/CONTRACT_TO_CODE_GAP_MATRIX.md`.

## Structural contract foundation

TASK-032A implements Draft 2020-12 structural schema validation for the seven
canonical TASK-030 schemas and an explicit assessment-only legacy compatibility
layer. Schema files remain in `schemas/`, are pinned by exact-byte hashes, and
are validated with active date/date-time format checking.

TASK-032A implements structural schema validation and legacy migration
assessment only. It does not implement delayed-response v1 DSL objects, actual
legacy conversion, parameter adapters, semantic verifier completion, runtime
behavior, method completion, or experimental validation. See
`docs/method/STANDARD_SCHEMA_REGISTRY.md`.

## Typed delayed-response document foundation

TASK-032B implements typed delayed-response rule documents and deterministic
serialization only. Parsing begins with the TASK-032A structural registry and
then enforces the frozen one-source/one-target delayed-response document shape.

Successful parsing, `status: accepted`, and document hashes do not provide
semantic verification or runtime authority. TASK-032B does not complete
parameter approval, graph/evidence binding, legacy migration, verifier stages,
runtime execution, the proposed method, or experimental validation. See
`docs/method/DELAYED_RESPONSE_RULE_V1_MODEL.md`.

## Typed external contract artifact foundation

TASK-032C implements typed external contract artifacts and explicit synthetic
Phase 1 adapters only. It adds immutable graph, evidence-package, and parameter
records, integrity-only canonical self-hashes, fail-closed explicit adapters,
and a non-authoritative lookup collection.

TASK-032C does not bind or approve rules, complete the deterministic verifier,
authorize runtime execution, complete the proposed method, or provide
experimental validation. See `docs/method/CONTRACT_ARTIFACT_HASH_POLICY.md`.
