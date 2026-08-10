# TASK-039C-INTEGRATE — Final Three-Arm Candidate Cohort Freeze

## Scope

Integrate the accepted public META, STAT, and compatibility-closed GDN top-20
candidate views under the TASK-039C0 `CandidateIntegrationPolicyV1`. The sole
scientific operation is `integrate_candidate_union_v1`: stable arm encounter
order (`META`, `STAT`, `GDN`), exact `(source, target)` de-duplication, and
per-arm evidence provenance.

The integration does not read HAI values or private ledgers, does not use BR2
pair outcomes, does not recompute an arm score, and creates neither a merged
score nor a global scientific rank.

## Frozen inputs

- C0: `b6522fb83c4cb92d355f98af778f9a6a3c73362f`
- META result: `b8a744c4b2cc70cd70bfc73ce45408c2ec8b5824`
- STAT result: `9359a8b8085b1948bde23171ec886e996fbd37b3`
- final GDN result: `1204ff4e6d790c2cd0e8268f778a8f071e5eea4b`
- preliminary META/STAT review: `058b5e2023b66ccbf6704c5baf1f6c677f17b07a`
- final GDN audit: `eab10dee0f08f419638154a9902304339b63c471`

The preliminary review is historical evidence for META and STAT. Its pre-GDNP
GDN availability conclusion is superseded by the passing final GDN audit.

## Expected frozen result

- arm counts: 20 / 20 / 20;
- pairwise intersections: 11 / 1 / 1;
- triple intersection: 0;
- origin decomposition: 8 META-only, 8 STAT-only, 18 GDN-only, 11 META+STAT,
  1 META+GDN, 1 STAT+GDN, 0 all-three;
- union: 47;
- audited preview hash:
  `81a7b6e0dfffdd6ce1b49799721c3dfcfb484af247a194d87b0602e76ac551ff`.

## Commit and execution discipline

Commit A freezes integration contracts, schemas, logic, runner, synthetic and
public-artifact tests, and pre-execution documentation. The public-only runner
must execute from a clean Commit A. Commit B may add only sanitized integration
outputs, result-instance tests, and completed-status documentation.

## Authority boundary

A passing integration authorizes TASK-039D0 protocol design only. It does not
authorize real profiling, train1/train2 profiling execution, train3
confirmation, train4/test/label/attack access, Rule v2, an Agent, detector or
runtime activity, or outer/sealed evaluation.
