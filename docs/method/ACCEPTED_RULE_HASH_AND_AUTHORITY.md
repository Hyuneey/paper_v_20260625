# Accepted Rule Hash and Authority

## Decision

DEC-041 defines two distinct rule hashes.

- The TASK-032B canonical document hash covers the complete serialized rule and
  is a transport/integrity hash.
- The verification-subject hash covers the canonical Rule v1 document after
  removing only top-level `status` and `verified_rule_hash`.

The verification subject uses UTF-8, sorted keys, compact separators, ASCII
escaping, finite JSON numbers, and SHA-256. All scientific content,
provenance, references, and complexity fields remain covered.

## Materialization

An accepted rule is materialized only from a `candidate` or `needs_repair`
document whose `verified_rule_hash` is null. The verifier deep-copies the
candidate, sets `status` to `accepted`, sets `verified_rule_hash` to the
verification-subject hash, and parses the result again through the TASK-032B
model. The candidate is never modified.

Acceptance requires:

```text
accepted_rule.verified_rule_hash
= verifier_result.rule_hash
= verification_subject_hash
```

The verifier-result `artifact_hash` is a separate DEC-040 self-hash that proves
the result document's integrity. Authority depends on an accepted result and
matching rule binding; a hash alone grants no authority.

## Runtime Boundary

TASK-032D never authorizes or executes a rule. Both accepted outcomes and
materialized accepted rules remain runtime-unauthorized. Runtime authorization
requires a later TASK-032E binding to the accepted verifier result and all
external artifact hashes.
