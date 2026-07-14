# Delayed-Response Verifier v1

## Scope

TASK-032D binds one typed delayed-response Rule v1 candidate to one typed
candidate graph, one evidence package, and approved calibration parameters. It
produces a deterministic canonical verifier-result and may materialize a new
accepted-rule document. It does not execute or runtime-authorize that rule.

## Ordered Stages

The verifier records every stage as `passed`, `failed`, or
`skipped_due_to_prior_failure`:

1. structural schema and artifact-hash validation
2. source/target type validation
3. graph variable allowlist
4. subsystem compatibility
5. directed candidate-edge binding
6. relation-family and evidence-claim compatibility
7. bounded unit compatibility
8. lag and parameter binding
9. window and persistence binding
10. parameter existence, approval, stability, and support
11. parameter provenance
12. split policy
13. evidence reference and selection policy
14. matched normal references
15. bounded document-level conflicts
16. structural duplicate and provable subsumption checks
17. declared MVP complexity budget
18. binary missing-response output contract
19. future explanation provenance completeness
20. claim and authority boundary

Only a structural failure skips later stages, because trustworthy typed inputs
are required for safe cross-artifact inspection. Other failures are accumulated
and deterministically sorted so one run returns the complete bounded feedback
set.

## Result Policy

- no violations: `accepted`
- only repairable violations: `needs_repair`
- any non-repairable violation: `rejected`

Per-stage orchestration issues carry repairability. The frozen canonical
verifier-result schema stores the corresponding aggregate field sets in
`repairable_fields` and `non_repairable_fields`; no schema change was made.
Only references that pass their relevant stages appear in `verified_*` fields.

Structural duplicates use a semantic document projection that excludes rule
identity, version, authority, provenance, and review history. Behavioral
duplicate claims are explicitly deferred because no rule execution occurs.

## Determinism and Boundaries

The verifier reads no clock; `created_at` and all policy limits are supplied.
Result IDs, issue ordering, accepted hashes, and self-hashes are deterministic
for identical inputs. Graph edges remain candidate relations, evidence cannot
contain raw values, test/validation provenance cannot fit numeric parameters,
and candidate authority preclaims are rejected.

No dataset, provider, ARGOS agent, generated Python, legacy verifier, legacy
runtime, or container is used.
