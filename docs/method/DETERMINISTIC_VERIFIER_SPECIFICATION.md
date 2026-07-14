# Deterministic Verifier Specification

## Authority

The verifier is deterministic code and has final acceptance authority. A Rule
Planner, Rule Reviewer, Explanation Renderer, or other LLM cannot override a
rejection. A revised candidate must enter the full verifier again.

## Ordered stages

1. JSON schema validation
2. type validation
3. variable allowlist validation
4. subsystem compatibility validation
5. graph-edge reference validation
6. relation-family compatibility validation
7. unit compatibility validation
8. lag-bound validation
9. window-bound validation
10. parameter existence and approval validation
11. parameter provenance validation
12. split-policy validation
13. evidence-reference validation
14. normal-reference validation
15. rule conflict detection
16. duplicate and subsumption detection
17. complexity-budget validation
18. output-contract validation
19. explanation-provenance validation
20. claim-boundary validation

Stages run in order and return structured issues. An earlier structural failure
may prevent later semantic checks, but the report records which stages ran.

## Result contract

`schemas/verifier_result_schema.json` records result/rule IDs and hashes,
verifier version, status, violations, warnings, mutable and immutable fields,
verified graph/parameter/evidence/normal references, complexity, conflicts,
duplicates, and timestamp.

Statuses are `accepted`, `rejected`, or `needs_repair`. `needs_repair` is not
runtime authorization.

## Repair classification

Repairable fields are limited to registered DSL structure whose references are
already approved. Non-repairable fields include rule identity, schema and
dataset versions, evidence and graph references, verified numeric values, and
final-test boundaries.

## Conflict and complexity

The verifier compares candidates against the accepted library for direct
conflict, structural duplicate, behavioral duplicate, and subsumption. The
initial complexity budget is at most 12 operators, 8 variables, depth 6, and
three review iterations. A lower task-specific budget may be preregistered.

## Hash rules

Canonical JSON hashing excludes only the artifact's own hash field. Accepted
rule, parameter, evidence, graph, and verifier hashes are verified again at
runtime. A changed dependency invalidates the accepted rule until reverified.
