# IMPLEMENTATION_PLAN.md

## 1. Objective

Build a feasibility-first prototype for graph-guided, training-time agentic verified rule construction for explainable multivariate time-series anomaly detection.

The deterministic scientific path must be proven before adding an LLM:

```text
local SWaT data + metadata
→ leakage-safe views and splits
→ candidate universe
→ masked GDN Top-K candidate pairs
→ normal relation profile and calibrated parameters
→ template DSL rule
→ deterministic verification
→ runtime LLM-free execution and explanation
```

Only after this path passes its gate may the LLM planner and verifier-feedback loop be implemented.

---

## 2. External references and dataset strategy

### ARGOS

- repo: `https://github.com/microsoft/ARGOS`
- role: architectural reference for planning/repair/review and runtime deterministic rules
- do not reuse:
  - univariate dataset contract,
  - test evaluation inside training loops,
  - arbitrary Python execution.

### GDN

- repo: `https://github.com/d-ailin/GDN`
- role: architecture reference for candidate-relation learning
- strategy: modern minimal port, not the legacy environment as the main dependency
- required change: candidate-universe mask before Top-K and candidate self-edge exclusion

### SWaT

- preferred data source: official iTrust distribution
- optional local mirror: researcher-provided Kaggle download
- raw data remains local-only under `SWAT_DATA_ROOT`
- TASK-000 must establish edition, version, schema, sampling period, and hashes

---

## 3. MVP assumptions

- primary dataset: SWaT
- first relation class: binary actuator → continuous sensor
- first trigger: actuator transition, initially `closed → open`
- first response: positive target change
- calibrated values:
  - maximum response delay,
  - minimum response magnitude
- minimal DSL:
  - `changed_to`,
  - `increase_within`,
  - `response_missing`
- runtime LLM calls: prohibited
- canonical rule view: highest approved resolution
- optional GDN view: independently configured and traceable

---

## 4. Recommended repository structure

```text
project/
├── AGENTS.md
├── IMPLEMENTATION_PLAN.md
├── README.md
├── THIRD_PARTY_NOTICES.md
├── configs/
│   ├── data/
│   ├── candidates/
│   ├── profiling/
│   └── experiments/
├── docs/
│   ├── tasks/
│   ├── ARCHITECTURE.md
│   ├── DATA_CONTRACTS.md
│   ├── DATASET_PROVENANCE.md
│   ├── UPSTREAM_SOURCES.md
│   ├── RESEARCH_INVARIANTS.md
│   ├── DECISIONS_REQUIRED.md
│   └── EXPERIMENT_PROTOCOL.md
├── external/                 # optional pinned references; no SWaT data
│   ├── argos/
│   └── gdn/
├── src/<package>/
│   ├── data/
│   ├── metadata/
│   ├── candidates/
│   ├── gdn/
│   ├── profiling/
│   ├── dsl/
│   ├── planning/
│   ├── verification/
│   ├── runtime/
│   └── evaluation/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/             # synthetic only
├── scripts/
└── artifacts/                # local/generated; raw data never copied here
```

TASK-000 must adapt this to the actual repository rather than creating a competing layout.

---

## 5. Dependency graph

```text
TASK-000
  └── TASK-001
      └── TASK-002
          └── TASK-003
              └── TASK-004
                  └── TASK-005 [Phase Gate A]
                      └── TASK-006
                          ├── TASK-007
                          │   └── TASK-008
                          │       └── TASK-009
                          │           └── TASK-010
                          │               └── TASK-011 [Phase Gate B]
                          │                   └── TASK-012
                          │                       └── TASK-013 [Phase Gate C]
                          │                           └── TASK-014
```

---

## 6. Milestones and gates

### Milestone 0 — Repository, upstream, and dataset readiness

**Ticket:** TASK-000

Deliverables:

- repository audit,
- exact install/test commands,
- upstream source and license register,
- GDN modern-port decision,
- ARGOS reuse boundary,
- SWaT dataset provenance and hash report,
- data-governance check,
- unresolved decisions register.

**Gate 0:** No source implementation begins until:

1. the target repository is understood,
2. SWaT is available locally or explicitly unavailable,
3. dataset edition/version status is recorded,
4. upstream commits and licenses are pinned,
5. environment strategy is approved.

---

### Milestone 1 — Leakage-safe data foundation

**Tickets:** TASK-001, TASK-002

Deliverables:

- `DatasetManifest`,
- canonical rule view,
- optional GDN view,
- raw-timeline split manifests,
- purge-gap windowing,
- variable metadata schema,
- synthetic test fixtures.

Acceptance:

- same input/config produces identical manifests,
- raw data is never copied into Git,
- split-before-windowing is enforced,
- test is rejected by training/calibration APIs,
- view and sampling period are explicit,
- invalid or unverified dataset assumptions are surfaced.

---

### Milestone 2 — Candidate universe and modern GDN extraction

**Tickets:** TASK-003, TASK-004, TASK-005

Deliverables:

- candidate universe with provenance,
- explicit candidate mask,
- modern GDN implementation or approved adapter,
- masked Top-K extraction,
- candidate self-edge exclusion,
- K/seed stability report,
- feasibility report.

#### Phase Gate A — Candidate feasibility

Proceed only if:

1. the pipeline runs reproducibly on normal data,
2. every candidate edge is proven to belong to `C_i`,
3. no persisted relation is a candidate self-edge,
4. candidate artifacts record source view and sampling period,
5. pre-registered relation recall/stability results justify further profiling,
6. no threshold was chosen on final test data.

A pass threshold must not be invented silently.

---

### Milestone 3 — High-resolution relation profiling and calibration

**Ticket:** TASK-006

Deliverables:

- trigger extraction,
- response detection,
- response-delay distribution in seconds,
- response-magnitude distribution,
- calibration records,
- structured evidence packs.

Acceptance:

- profiling uses canonical rule view,
- time conversion references `sampling_period_seconds`,
- calibration uses `calibration_normal`,
- insufficient support returns an explicit unsupported status,
- synthetic fixtures verify delays exactly,
- no test information is used.

---

### Milestone 4 — Deterministic rule path

**Tickets:** TASK-007, TASK-008, TASK-009, TASK-010, TASK-011

Deliverables:

- JSON/AST DSL and schema registry,
- no arbitrary code execution,
- deterministic template planner,
- deterministic verifier feedback,
- runtime LLM-free engine,
- validation-only end-to-end feasibility report.

#### Phase Gate B — Deterministic feasibility

Proceed to LLM integration only if:

1. candidate → profile → rule → verification → runtime alarm works,
2. runtime has no LLM or dynamic-code dependency,
3. numeric parameters trace to calibration artifacts,
4. normal firing and validation coverage are measurable,
5. restricted data never enters Git or prompts,
6. the final test remains sealed.

---

### Milestone 5 — Agentic LLM rule construction

**Tickets:** TASK-012, TASK-013

Deliverables:

- provider-neutral LLM interface,
- mock provider for tests,
- structured JSON planning output,
- prompt/model provenance,
- bounded verifier-feedback refiner loop,
- revision history,
- template/one-shot/refined comparison.

#### Phase Gate C — Demonstrated LLM value

Proceed to broad evaluation only if the experiment can distinguish:

```text
Template-only
vs
One-shot LLM
vs
LLM + verifier feedback
```

The report must state when LLM use adds no material value.

---

### Milestone 6 — Sealed evaluation and optional fusion

**Ticket:** TASK-014

Deliverables:

- pre-registered evaluation config,
- one-way final test execution,
- PA-free/range/event metrics,
- candidate and explanation metrics,
- optional detector fusion isolated from the primary method,
- case study and limitations.

Acceptance:

- no test-tuned choices,
- point adjustment is off by default,
- any supplementary point-adjusted result is clearly labeled,
- detector performance and explanation quality are reported separately,
- failed and unsupported cases are included.

---

## 7. Key decisions that TASK-000 must resolve

1. **GDN strategy**
   - preferred: modern PyTorch/PyG port with behavioral tests,
   - alternative: legacy isolated container for reference only.
2. **SWaT source**
   - official iTrust preferred,
   - Kaggle mirror permitted only after provenance verification.
3. **Sampling strategy**
   - canonical high-resolution rule view,
   - optional downsampled GDN view.
4. **ARGOS reuse scope**
   - architecture and agent concepts only,
   - no univariate dataset contract or arbitrary Python execution.
5. **Evaluation protocol**
   - final test sealing,
   - approved PA-free/range/event metrics.

---

## 8. Definition of done for every ticket

A ticket is complete only when:

1. acceptance criteria are met,
2. relevant tests pass,
3. lint/type checks pass where configured,
4. artifacts include required provenance,
5. no restricted data is tracked,
6. no research invariant is violated,
7. exact commands and results are reported,
8. unresolved decisions are documented,
9. the next ticket is recommended or explicitly blocked.
