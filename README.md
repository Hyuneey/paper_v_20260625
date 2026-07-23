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

## Deterministic delayed-response binding foundation

TASK-032D implements the twenty-stage deterministic MVP binding verifier. It
can bind a delayed-response candidate to one candidate graph, one evidence
package, and approved stable parameters, then materialize an accepted Rule v1
document with a non-circular authority hash.

Acceptance is not runtime authorization. TASK-032D does not execute rules,
produce runtime traces or explanations, modify the legacy Phase 1 verifier or
runtime, access datasets, call providers, or establish experimental method
performance. See `docs/method/DELAYED_RESPONSE_VERIFIER_V1.md`.

## Authorized synthetic runtime foundation

TASK-032E implements an authorized synthetic delayed-response runtime and
deterministic trace-grounded explanation only. Execution requires a receipt
that revalidates the TASK-032D accepted rule, verifier result, verifier policy,
and exact graph/evidence/parameter bindings.

The runtime emits a canonical nine-step satisfaction trace and deterministic
explanation without an LLM. This does not imply real SWaT execution, anomaly-
detection performance, calibrated severity quality, detector fusion, complete
method implementation, or thesis-result completion. See
`docs/method/RUNTIME_AUTHORIZATION_BINDING.md`.

## Deterministic synthetic vertical-slice gate

TASK-032F completes a deterministic synthetic delayed-response contract
vertical slice. It starts from serialized synthetic Phase 1 mappings, uses the
explicit adapters, verifies a predeclared candidate through all twenty stages,
creates a fresh runtime authorization, and reproduces eight canonical
trace/explanation outcomes with identical hashes across two fresh runs.

This does not establish real dataset execution, learned graph quality,
rule-generation quality, calibration validity, detection performance,
explanation usefulness, complete method implementation, or thesis completion.
See `docs/method/SYNTHETIC_DELAYED_RESPONSE_VERTICAL_SLICE.md`.

## ARGOS E1 isolated runtime smoke

TASK-033 re-enters the deferred container track through a new WSL-native
rootless Podman decision; it does not resume TASK-028 or retry Docker Desktop.
One frozen captured ARGOS rule was executed only inside network-disabled,
read-only, resource-bounded Linux containers against four repository-owned
synthetic non-KPI fixtures.

The three required non-empty fixtures satisfied the output length, finite
binary-domain, and fresh-container replay checks; the empty diagnostic fixture
also returned a deterministic empty output. This establishes container/runtime
plumbing only. It does not establish anomaly-detection performance, KPI or SWaT
behavior, RepairAgent or ReviewAgent effects, detector fusion, benchmark
reproduction, or thesis results. See
`docs/argos_reproduction/ARGOS_E1_RUNTIME_PROTOCOL.md`.

## ARGOS E2 validation-only gate

TASK-034 Commit A implements the guarded KPI validation split, dedicated
rootless-container execution harness, PA-free array diagnostics, and separately
labeled source-faithful ARGOS metric adapter. The held-out test boundary is
sealed by a prefix reader and the container can receive validation values only.

E2 ran from clean execution commit `b81468c4` and passed the validation
feasibility gate with identical prediction hashes from two fresh containers.
Its direct metrics are PA-free validation diagnostics and the source-faithful
ARGOS metrics are supplementary validation diagnostics. E3 remains `not_run`,
`sealed_not_accessed`, and `not_authorized`. Neither stage is a benchmark or
thesis-performance claim. See
`docs/argos_reproduction/ARGOS_E2_KPI_VALIDATION_PROTOCOL.md`.

## ARGOS E2X-G expanded generation cohort

TASK-035A implements the pre-registered E2X-G preparation and execution gate:
10 eligible KPI series, five deterministic anomaly-anchored generation chunks
per series, and two identical one-shot provider requests per anchor. The
implementation freezes all 100 requests before network access, consumes each
slot at most once, performs deterministic static checks, and permits only
rootless-container runtime-contract checks on generation values.

TASK-035A does not compute KPI validation performance. Inner selection,
outer validation, ensemble evaluation, detector/fusion experiments, and sealed
test access remain deferred or unauthorized. Raw prompts, responses, rules,
arrays, and outputs remain ignored private artifacts. See
`docs/argos_reproduction/EXPANDED_KPI_COHORT_PROTOCOL.md`.

The bounded E2X-G run completed all 100 slots but ended
`insufficient_rule_yield`: 84 responses contained text, 61 rules passed static
checks, and 55 rules passed isolated shape/domain runtime checks. These are
generation and plumbing yields, not anomaly-detection metrics. No retry,
repair, inner/outer validation, or sealed-test access followed.

## ARGOS E2X-GR output-budget remediation

TASK-035AR pre-registers a separate balanced 100-slot remediation cohort using
the same ten KPIs, fifty anchors, and exact TASK-035A prompt bytes. Every anchor
receives replicate IDs 3 and 4. The only generation change is increasing
`max_output_tokens` from 2,000 to 6,000; provider, model, prompt, static audit,
and rootless-container runtime policies remain unchanged.

The clean Commit A-R execution completed all 100 one-shot calls: all responses
were non-empty and static-valid, and 91 rules passed the isolated runtime
contract. Combined with the immutable TASK-035A cohort, 146 rules were
executable and every frozen balance threshold passed.

This is a generation-operability and cohort-balance result only. It does not
compute validation or test performance, perform selection, repair rules, run a
detector or fusion path, or alter TASK-035A's `insufficient_rule_yield` status.

## ARGOS E2X-S/V balanced multi-rule validation

TASK-035B implements the predeclared values-only full-inner runtime gate,
label-independent balanced panel, direct PA-free metrics, four-arm inner
selection, frozen outer-validation runner, and paired KPI bootstrap. Execution
uses the required Commit A / Commit B / Commit C separation. The held-out test
remains sealed, and no provider, rule-generation, detector, repair, review, or
fusion path is authorized.

The frozen outer run completed for all ten KPI series. Coverage-3 OR showed
higher macro recall than Best-1 but lower point F1 and precision with a much
higher false-positive rate. This is a validation tradeoff, not evidence of
multi-rule superiority or a benchmark/thesis result. E2X-T remains sealed and
unauthorized.

Professor-facing prototype evidence package:
[Prototype Progress Report](docs/professor_feedback/PROTOTYPE_PROGRESS_REPORT.md).

## ARGOS detector provenance freeze

TASK-037A identifies ARGOS's KPI detector family as LSTMAD but preserves the
unresolved official EasyTSAD `LSTMADalpha`/`LSTMADbeta` variant ambiguity as a
dual-arm, non-selected sensitivity design. Both variants passed an isolated
synthetic-only rootless-container smoke.

No real KPI detector training, scoring, threshold selection, outer validation,
fusion, or sealed-test access was performed. E4/E5/E6 remain protocol-frozen
and unauthorized. See
[`ARGOS_KPI_BASE_DETECTOR_AUDIT.md`](docs/argos_reproduction/ARGOS_KPI_BASE_DETECTOR_AUDIT.md).

## ARGOS E4 dual LSTM detector validation

TASK-037B freezes a commit-separated detector-only run for both official
EasyTSAD LSTMAD variants across the existing ten KPI series. It uses
generation-only fitting, inner-only threshold selection and one-way outer
validation without selecting a variant. Detector-rule fusion and every sealed
test remain unauthorized. See
[`LSTM_DETECTOR_EXECUTION_PROTOCOL.md`](docs/argos_reproduction/LSTM_DETECTOR_EXECUTION_PROTOCOL.md).
