# TASK-039E3 R2R Utility Protocol V3 Final Remediation

Status: `passed_task039e3_r2r_utility_protocol_v3_final_remediation`

Protocol V3 is an additive closure over immutable V1 and V2. It closes only the two blockers explicitly reopened on 2026-08-19. It does not read HAI test features or labels, compute utility, contact a provider, or grant execution/runtime authority.

## Opportunity custody closure

The primary policy is `FULL_CENSUS_NO_FIXED_SAMPLE_SIZE`. Every source event surviving the frozen complete-context, threshold/stability, same-source clustering, exact 12-source isolation, and expected-direction pipeline forms one opportunity for each accepted relation cell. Source failures before formation and `no_rule` cells do not enter the opportunity custody or abstention denominator.

`OpportunityCustodyV3` stores the canonically ordered terminal record for every enumerated opportunity and recomputes every summary count from those records. `abstention_rate_from_custody_v3` accepts only the custody object. The synthetic oracle contains five records, three evaluated and two abstained, so the derived rate is exactly 2/5 = 0.4. A caller-supplied 1/999 path is absent by function signature.

## Type and state closure

The metadata-only P1 schema binds 12 exact sources and 10 exact COMMON targets. Continuous features use one strict decimal-token parser at the raw boundary and canonical finite floats internally. No missing token or nonfinite value is authorized; units remain unbound rather than inferred. Tagged available contexts require exact 5/5 source and 5/3 target windows, while unavailable contexts carry reasons and no values.

Validation of identities, types, schema, lengths, parameters, directions, and coordinates occurs before scientific boundary or response states. Malformed source/target values therefore raise `UtilityProtocolV3Error`; they cannot become source-not-formed, `abstain`, or another scientific result. Valid physical/split boundaries preserve the frozen source-not-formed and abstention behavior.

## Scientific regression and authority

COMMON remains 42/42 executable-equivalent, T2 remains 39/39 for accepted cells with three preserved `no_rule` cells, and numeric reference closure remains 420/420. Continuous-step semantics, primary metrics, point-adjustment prohibition, construction call counts, Direct-number exclusion, and exploratory candidate-origin status are unchanged.

V1 and V2 sources are byte-identical to their frozen authorities. Construction scientific source and result artifacts were not modified. The canonical authority is `BASE_V1_PLUS_REMEDIATION_V2_PLUS_FINAL_CLOSURE_V3` with status `FROZEN_PENDING_FINAL_FOCUSED_AUDIT`.

Focused validation recorded 27/27 new V3 tests and 58/61 historical regression tests passing; three historical private-input tests were skipped because the private registry/E1 ledger was deliberately not configured for this zero-private-access remediation. `compileall`, `pip check`, JSON parsing/self-hashes, source blob/byte checks, sensitive-data scan, and Git diff checks passed.

## Boundary and next gate

- HAI test feature values accessed: 0
- HAI label values accessed: 0
- attack intervals accessed: 0
- utility values computed: 0
- provider/scientific calls: 0
- `UTILITY_PROTOCOL_AUDITED`: false
- `UTILITY_EVALUATOR_IMPLEMENTATION_READY`: false
- `UTILITY_EXECUTION_AUTHORIZATION_READY`: false

Exact next task: `TASK-039E3-R2R-UTILITY-PROTOCOL-V3-FOCUSED-INDEPENDENT-AUDIT`.
