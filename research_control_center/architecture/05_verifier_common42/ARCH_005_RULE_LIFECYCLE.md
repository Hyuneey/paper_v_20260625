# ARCH-005 Rule Lifecycle

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

The source contains two distinct authority planes. They share concepts but are not one continuous object lifecycle.

## Construction and frozen D1 plane

| State | Object | Producer | Consumer / authority | Failure |
|---|---|---|---|---|
| confirmed relation | `ConfirmedRelationPrimitiveV1` | normal profiling/confirmation | E3 evidence materialization | fail closed on identity mismatch |
| construction view | frozen E3 relation/evidence view | E3 bridge | T0/T1/T1-B/T2 | construction input rejection |
| proposal | closed TASK-039E mapping | template/provider arm | `verify_prepared_rule_proposal_v2` | explicit validity issues |
| task admissible | `PreparedValidityResultV2(status=admissible)` | task validity V2 | E0 result freeze | otherwise rejected |
| executable equivalence | one projection per relation | utility protocol audit | COMMON-42 selection | mismatch excluded/fails |
| V4 descriptor | `CanonicalRuleDescriptorV4` | V4 authority replay | evaluator authority | exact replay required |
| portfolio frozen | `UtilityProtocolV4CanonicalAuthority` + full census plan | V4 factory | evaluator/D1 grant | stale identity rejected |
| D1 authorized | committed D1 grant and process-local token | D1 authorization bridge | real D1 evaluator | one attempt; exact scope |
| executable | task-specific deterministic real evaluator | D1 bridge | frozen prediction | mismatch or missing context fails/abstains as defined |

## General canonical contract plane

| State | Object | Producer | Consumer / authority | Failure |
|---|---|---|---|---|
| canonical candidate | `DelayedResponseRuleV1(status=candidate)` | canonical parser | `verify_delayed_response_rule` | structural error |
| verifier outcome | `RuleVerificationOutcomeV1` | 20-stage `VerifierV1` | accepted-rule materializer | accepted / needs_repair / rejected |
| canonical accepted rule | `DelayedResponseRuleV1(status=accepted)` | verifier | governance/runtime authorization | never runtime-authorized by itself |
| runtime bundle | `RuntimeAuthorizationBundleV1` | `runtime_authority.py` | canonical synthetic runtime | exact binding or fail closed |

No tracked bridge materializes the frozen TASK-039E proposals into `DelayedResponseRuleV1`, applies `VerifierV1`, and then supplies those objects to frozen D1. Therefore the two planes are `PARTIALLY_OVERLAPPING` and `NON_EQUIVALENT_BY_DESIGN`.
