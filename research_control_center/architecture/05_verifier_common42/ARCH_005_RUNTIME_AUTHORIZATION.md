# Runtime Authorization Boundary

## General canonical contract

`paperworks.contracts.runtime_authority` authorizes only an accepted `DelayedResponseRuleV1` whose accepted verifier result, graph/evidence/parameter collection, governance selection, deployment receipt and hashes all replay exactly. `VerifierV1` acceptance alone never grants execution. The current general bundle is synthetic-only and fails closed on mismatch.

## Frozen D1

Frozen D1 does not use that bundle. It uses a separate, task-specific authority plane:

1. exact V4 COMMON-42 authority replay;
2. evaluator authority bundle and implementation identity;
3. private numeric resolver custody bound to the public registry identities;
4. committed INNER D1 execution grant and one-attempt token;
5. automatically enumerated full census with no caller thresholds or outcome knobs;
6. label-blind prediction artifact before label loading.

`execute_real_rule_v1` validates the V4 opportunity, descriptor and ten numeric bindings before deterministic evaluation. Any stale descriptor, reference set, registry or grant mismatch raises a bounded error. Therefore stale authority cannot execute through the audited entrypoint, but this protection is task-specific rather than proof that canonical `RuntimeAuthorizationBundleV1` governed D1.
