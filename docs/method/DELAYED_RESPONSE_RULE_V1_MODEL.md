# Delayed-Response Rule v1 Model

## Scope

TASK-032B provides an immutable typed representation for the delayed-response
MVP defined by TASK-030 and frozen by DEC-036. Parsing is limited to one source
variable, one target variable, a `state_changes_to` trigger, an increasing
`delayed_change` effect, and a `missing_expected_response` binary output.

The model is a document representation only. It does not resolve graph edges,
evidence packages, normal references, parameters, units, dataset splits, or
subsystem metadata.

## Registry-First Parsing

`parse_delayed_response_rule()` always validates the input with the TASK-032A
`rule_dsl` registry before constructing typed values. Draft 2020-12 structural
failures become a sanitized `RuleV1ModelError` containing a stable issue code,
field path, message, and structural-report hash.

After structural validation, the parser applies only bounded intra-document
MVP checks:

- relation, source, and target cardinality;
- trigger/source and effect/target consistency;
- delayed-response direction and output semantics;
- fixed or interval lag consistency;
- event-relative or persistence window support;
- persistence reference consistency;
- nested parameter-reference closure.

External identifier existence and scientific approval remain future
deterministic-verifier responsibilities.

## Typed Records

The primary representation is `DelayedResponseRuleV1`, composed of frozen
dataclasses for operating regime, trigger, expected effect, lag, window,
persistence, output semantics, severity, abstention, complexity, provenance,
and review history. JSON arrays become tuples and undeclared properties are
rejected by the canonical schema.

Every field in `rule_dsl_schema.json` has an explicit model location. No
generic mapping is retained as the internal rule representation.

## Authorization Boundary

Structural validity and successful parsing do not approve a rule. In
particular, serialized `status`, `verified_rule_hash`, and
`provenance.candidate_hash` are untrusted document values until a future
verifier result binds them.

`DelayedResponseRuleV1.runtime_authorized` is hard-coded to `False` and is not
serialized. TASK-032B objects cannot be executed by the runtime.

## Exclusions

TASK-032B does not implement legacy conversion, graph/evidence/parameter
binding, parameter approval, the twenty verifier stages, rule execution,
explanation rendering, LLM activity, or experimental evaluation.
