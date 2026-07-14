# Delayed-Response Context Collection

`DelayedResponseArtifactCollectionV1` is an immutable lookup container for one
candidate graph, one evidence package, and one or more calibration parameters.
It exposes deterministic indexes for graph, edge, evidence, normal-reference,
and parameter IDs and rejects duplicate parameter IDs.

The collection is intentionally non-authoritative:

- it does not bind a rule to an edge, evidence package, or parameter;
- it does not decide cross-artifact compatibility;
- it does not approve a rule or produce a verifier result;
- `rule_binding_verified` and `runtime_authorized` are always false and are not
  serialized.

Future TASK-032D verifier stages must perform graph, evidence, parameter,
split, unit, status, and hash binding before any rule may be accepted.
