# Verifier Stage Implementation Map

The table evaluates semantics, not naming similarity.

| # | TASK-030 stage | Current state | Existing basis | Missing for v1 | Priority |
|---:|---|---|---|---|---|
| 1 | JSON schema validation | partial | `parse_rule_json`, `RuleAst.from_dict` | Draft 2020-12 validator and schema-version registry | P0 |
| 2 | Type validation | partial | one actuator-binary to sensor-continuous check | all typed v1 fields and references | P0 |
| 3 | Variable allowlist | complete for legacy pair | `RuleSchemaRegistry` metadata lookup and predicate alignment | v1 graph/evidence variable registry | P0 |
| 4 | Subsystem compatibility | missing | metadata contains subsystem | explicit compatibility policy | P0 |
| 5 | Graph-edge reference | missing | only an opaque candidate-pair hash exists | resolve edge IDs and endpoints | P0 |
| 6 | Relation-family compatibility | partial | one hard-coded legacy family | registry-driven delayed-response constraints | P0 |
| 7 | Unit compatibility | partial | calibration reference/record unit equality | node, effect, lag and parameter dimensional checks | P0 |
| 8 | Lag-bound validation | partial | positive calibrated delay and evaluation bound | lag type/range/graph candidate limits | P0 |
| 9 | Window-bound validation | missing | implicit evaluation span | typed window and alignment checks | P0 |
| 10 | Parameter existence/approval | partial | calibration record existence | registry status must be `approved` | P0 |
| 11 | Parameter provenance | partial | name, unit, value and support integrity | split, method, stability, hashes and approvals | P0 |
| 12 | Split-policy validation | partial | test rejection; calibration/validation operation guards | cross-artifact split lineage | P0 |
| 13 | Evidence-reference validation | missing | relation evidence used by planners only | referenced evidence IDs/hashes | P0 |
| 14 | Normal-reference validation | missing | aggregate normal support only | matched normal reference IDs and policy | P0 |
| 15 | Rule conflict detection | missing | none | semantic conflict records | P1 |
| 16 | Duplicate/subsumption | partial | structural and firing-overlap duplicate checks | typed subsumption and provenance | P1 |
| 17 | Complexity budget | missing | fixed legacy shape incidentally bounds complexity | explicit budget and score | P1 |
| 18 | Output contract | partial | legacy evaluator returns binary anomaly aggregate | v1 output type, alignment and abstention | P0 |
| 19 | Explanation provenance | missing | runtime formats a mixed explanation | explanation-record reference closure | P1 |
| 20 | Claim-boundary validation | missing | repository policy only | artifact-level claim boundary checks | P1 |

`VerificationDataset` prohibits `test`, and `_assert_verification_splits` uses
operation-specific split guards for normal profiling and validation
verification. This is useful but does not prove end-to-end split provenance.
`VerificationReport` has only `passed`/`rejected`; v1 also requires
`needs_repair`, verified reference sets, complexity, conflicts, warnings, and
repairability fields.
