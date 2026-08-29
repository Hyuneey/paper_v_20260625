# ARCH-000 Legacy, Duplicate, and Gap Index

| Path / symbol | Category | Evidence | Current risk | Future action |
|---|---|---|---|---|
| `src/paperworks/dsl/*` | LEGACY | AGENTS compatibility boundary | Accidental reuse | Preserve read-only; inspect only if compatibility work is authorized |
| `src/paperworks/verification/*` | LEGACY | AGENTS compatibility boundary | Duplicate authority confusion | Keep separate from v6 verifier |
| `src/paperworks/runtime/*` | LEGACY | AGENTS compatibility boundary | Runtime identity confusion | Keep separate from v6 and canonical runtime |
| `src/paperworks/planning/refiner.py` | LEGACY | AGENTS compatibility boundary | Old planner mistaken for T2 | Document, do not reuse |
| `src/paperworks/e2e/*` | LEGACY | AGENTS compatibility boundary | Historical orchestration mistaken for current | Preserve only |
| `experiments/argos_reproduction/*` | REFERENCE_ONLY | Frozen reference policy | Reference mistaken for current method | Keep frozen |
| `candidate_discovery_protocol_v1.py` beside generic universe | DUPLICATE_ENTRYPOINT | Frozen C0 uses the v6 protocol | Wrong representative source | Review in ARCH-002 |
| canonical verifier beside `task039e0_validity_v2.py` | DUPLICATE_ENTRYPOINT | Executed construction uses task verifier | Authority relationship unclear | Review in ARCH-004/005 |
| canonical/synthetic/real runtime layers | DUPLICATE_ENTRYPOINT | Frozen D1 uses real bridge | Semantic drift risk | Review in ARCH-006/008 |
| construction mock orchestration / scientific projection / recovery generations | DUPLICATE_ENTRYPOINT | Real construction composes bounded mock semantics, private scientific projection, and a final successful V3 recovery lineage; earlier recovery generations are superseded | A single orchestration file can be mistaken for the complete executed path | Review controller ownership and recovery lineage in ARCH-004 |
| canonical `RuntimeTraceV1` to real D1 | MISSING_LINK | Direct typed edge not found | Trace documentation can overstate result lineage | Review in ARCH-006/008 |
| explanation renderer to frozen D1 | IMPLEMENTED_NOT_USED | No frozen-result call found | Human-usefulness claims unsupported | Evaluate separately |
| OUTER execution | DESIGN_ONLY | Blocker only; no result | Generalization unavailable | New preregistration only |
| fresh-machine reproduction | MISSING_LINK | Assessment says incomplete | Reproduction claim unavailable | Rehearse separately |
