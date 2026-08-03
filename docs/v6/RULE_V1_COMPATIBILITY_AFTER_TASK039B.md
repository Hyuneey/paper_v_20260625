# Rule V1 Compatibility After TASK-039B

The effective Rule v1 parser, verifier path, and runtime require:

- exactly one source and one target;
- relation type `delayed_response`;
- trigger type `state_changes_to`;
- a literal `state_value`;
- null trigger threshold, range, and duration references;
- expected direction `increase`;
- violation direction `missing_expected_response`.

The JSON schema contains broader transport alternatives, but the frozen MVP
parser rejects those alternatives and the verifier/runtime authority path is
bound to the parsed delayed-response semantics.

A continuous-control-step trigger cannot be introduced as metadata alone. Its
classification is:

`requires_versioned_rule_semantics`

TASK-039BR0 does not change Rule v1, its schema, verifier, runtime, TASK-032
fixtures, or any historical hash.
