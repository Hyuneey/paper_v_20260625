# Canonical Rule Schema

The general canonical representation is `paperworks.contracts.rule_v1.DelayedResponseRuleV1`, schema version `1.0.0`, artifact type `rule_dsl`. It is typed data, not Python source.

Required semantic groups include rule/dataset/subsystem and operating-regime identity; one source and one target; trigger, effect, lag, window and persistence structures; parameter, graph-edge, evidence and normal-reference identities; output, severity, abstention and complexity policies; review history and authority fields.

The current canonical MVP is narrower than the TASK-039E proposal core: it requires a delayed-response rule with `state_changes_to`, one distinct source/target, an expected `increase` effect, binary anomaly output and `missing_expected_response` semantics. A candidate has no verified-rule hash; an accepted rule binds the verification-subject hash. `runtime_authorized` remains false.

## Proposal versus canonical Rule

The TASK-039E proposal fixes a confirmed relation, source/target signs, one horizon, reference-only numeric identities, construction arm, provenance and budget. It omits much of the canonical graph/evidence/parameter/policy envelope. Conversely, canonical Rule v1 lacks TASK-039E arm, budget and relation-binding fields. No lossless tracked transformation was found.

Arbitrary Python, dynamic evaluation, file/network actions and free-form causal claims are not fields in the canonical schema.
