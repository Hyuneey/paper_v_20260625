# Scientific kernel map

## Minimal thesis kernel

| Layer | Classification | Representative remote modules |
|---|---|---|
| data and split contracts | CANONICAL_FINAL | `src/paperworks/data/contracts_v2.py`, `splits_v2.py`, `hai_provenance_v1.py` |
| candidate discovery | CANONICAL_FINAL | `candidates/*_candidate_discovery_v1.py`, `candidate_integration_v1.py`, `gdn/upstream_candidate_backend_v1.py` |
| temporal profiling | CANONICAL_FINAL | `v6/continuous_step_protocol_v1.py`, `v6/relation_profiling_protocol_v1.py`, `profiling/task039d1_fit_v1.py`, `task039d2_confirmation_v1.py` |
| normal evidence | CANONICAL_FINAL | `v6/normal_evidence_v1.py`, `contracts/normal_evidence_binding_v1.py` |
| rule and parameter contracts | CANONICAL_FINAL | `contracts/rule_v1.py`, `parameter_v1.py`, `canonical_collection_v1.py` |
| deterministic verification | CANONICAL_FINAL | `contracts/verifier_v1.py` and task039e0 validity adapters |
| execution and explanation | CANONICAL_FINAL | `contracts/runtime_v1.py`, `explanation_v1.py`, utility rule engine/runtime modules |
| D0/D1/D2 and metrics | CANONICAL_FINAL | task039e3 R2R D0, D1, D2 V1/V2 execution modules and utility metric policy |
| hashing, schema, adapters | REUSABLE_SUPPORT | `v6/common.py`, artifact hashing, schema registries, v2 adapters |
| ARGOS reproduction | HISTORICAL_REFERENCE | `experiments/argos_reproduction/*`, TASK-022–038 reports |
| old DSL/verifier/runtime/e2e | LEGACY_COMPATIBILITY | import-compatible paths identified in `AGENTS.md` |
| task-specific authorization/custody/reporting | TASK_SPECIFIC_GOVERNANCE | task039e3 authorization, recovery, custody, finalization, and audit modules |

The architecture is implemented in executable modules, not only described in
task specifications. Its reusable scientific center is nevertheless surrounded
by substantial task-specific governance code. A future release can package the
kernel more cleanly, but that cleanup is not needed before professor review.
