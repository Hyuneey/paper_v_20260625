# TASK-039E3 R2R Utility Protocol V3 Focused Independent Audit

Status: `blocked_task039e3_r2r_utility_protocol_v3_focused_independent_audit`.

The focused audit did not repair V3. It used synthetic fixtures only and found that both historically open blockers remain open at authoritative boundaries.

## What passed

- The canonical timeline implementation matched an independently derived 14-opportunity synthetic census exactly.
- `abstention_rate_from_custody_v3` accepts custody only; the 5-record fixture produced a record-derived `2/5 = 0.4` result.
- All 15 required serialized-custody mutations were rejected.
- No fixed sample-size field was found, and `no_rule` and source-not-formed states were excluded from the tested custody.
- Strict raw token and label parsing, exact float-window shapes, and direct source/target boundary-masking cases passed for a trusted feature schema.
- Lower frozen authorities yielded exactly 12 sources, 10 targets, and 22 required features with no missing or ambiguous type authority.
- COMMON 42/42, T2 accepted 39/39, T2 no_rule 3/3, numeric references 420/420, and the frozen continuous-step semantics were unchanged.
- V1, V2, V3 production source, construction source, and construction results were not modified.

## Blocking findings

1. Exact T2 accepted/no_rule membership is not bound; counts can be satisfied with foreign relation hashes.
2. Opportunity records are not replay-bound to the executable signature's source and target.
3. Caller source-keyed thresholds and tolerances can change the census without exact numeric-reference authority.
4. A caller can directly fabricate a `FullCensusEnumerationV3` accepted by the custody builder.
5. A self-consistent serialized feature schema can substitute an unknown target or metadata authority hash.
6. Integer parameters and floating row counts can cross the canonical scalar boundary.
7. A caller-created terminal abstention can be recorded for an interior opportunity without coordinate-derived provenance.
8. The V3 regression artifact contains three component authority hashes that do not match the committed authorities.

The first four findings leave the custody-derived denominator scientifically under-authorized. Findings five through seven leave fail-closed type/state authority incomplete. Finding eight breaks the public regression authority binding.

## Boundary record

HAI test feature values accessed: 0. HAI label values accessed: 0. Attack intervals accessed: 0. Utility values computed: 0. Provider calls: 0. API-key access: false. Scientific LLM calls: 0.

No automatic remediation loop or evaluator implementation is authorized by this blocked result.
