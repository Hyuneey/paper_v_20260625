# TASK-039E3 R2R Utility Normal-Only Authority V1 Feature-Scope Reconciliation

Status: PASS

The previous materialization stopped before HAI path resolution, value access, or a canonical materializer invocation. Public-only replay now establishes that the two counts describe different, compatible scopes.

## Reconciled scopes

The historical V3 evaluator schema remains a 12-source, 10-target, 22-feature authority for source-event and opportunity evaluation. The exact frozen COMMON-42 relation authority uses 9 of those sources, the same 10 targets, and therefore a 19-feature calibration/materialization footprint.

The V3-only source identities are:

- `P1_FCV02Z`
- `P1_PCV02Z`
- `P1_PP04`

All three remain legitimate V3 source-universe members. None appears as `relation.source` in COMMON-42. COMMON targets exactly equal the V3 target scope, and no COMMON feature is missing from the V3 schema.

## Authority replay

- COMMON relations: 42
- Utility numeric roles: 10
- Utility numeric references: 420
- Historical bindings: 462
- Excluded utility role: `selected_delay_horizon_seconds`
- Authority-definition hash: `6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de`
- Calibration-policy hash: `4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881`
- COMMON executable-equivalence hash: `3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f`

The normal-only implementation derives its exact required feature mapping as the union of `relation.source` and `relation.target`, rejects extra or missing mapping keys, and calibrates unique relation sources and targets. It does not use the broader V3 count as materialization selection logic.

## Authorization continuity

Authorization artifact `dad4d6c39d5f317bed41fe3f780d4bb20bd7b33aea047b9a166614ac4acf42b9` validates and binds the scientific authority, calibration policy, executable equivalence, normal-input identity set, train identities, and audited control source. It contains no fixed 12-source or 22-feature materialization requirement.

`AUTHORIZATION_REISSUE_REQUIRED = false`

## Decision

Feature-scope reconciliation changes the materialization work-order expectation only. It does not change V3, COMMON-42, the scientific authority definition, calibration semantics, relation membership, or numeric-reference identities.

No HAI value, test value, label, utility result, provider, API key, or scientific LLM was accessed during reconciliation.
