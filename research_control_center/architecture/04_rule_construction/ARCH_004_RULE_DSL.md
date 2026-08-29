# ARCH-004 Rule DSL Boundary

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Two related contracts

The construction experiment does not let the provider author an arbitrary full runtime rule. It first accepts a closed `ProviderProposalCoreV1` whose DSL family is `canonical_delayed_response_rule_v1_candidate`. Project code adds arm and provenance fields and forms a `RuleProposalEnvelopeV1`; `task039e0_validity_v2` then checks the envelope. The richer canonical `DelayedResponseRuleV1` / `schemas/rule_dsl_schema.json` contract exists downstream, but E3 explicitly records `canonical_rule_materialized=false` and `runtime_authority_granted=false`.

## Proposal-core schema

Required fields bind exactly one relation: relation identity, source and source direction, target and target direction, selected horizon, three calibrated numeric references, seven window-constant references, exactly the source/target variable pair, fixed DSL family, and fixed `missing_expected_delayed_response` runtime-logic family. Unknown fields are rejected.

Sanitized generic example:

```json
{
  "dsl_family": "canonical_delayed_response_rule_v1_candidate",
  "relation_identity": "RELATION_REFERENCE",
  "source": "SOURCE_ID",
  "source_step_direction": "step_up",
  "target": "TARGET_ID",
  "target_response_direction": "increase",
  "selected_delay_horizon_seconds": 10,
  "source_threshold_reference": "HASH_REFERENCE",
  "source_stability_reference": "HASH_REFERENCE",
  "target_scale_reference": "HASH_REFERENCE",
  "window_constant_references": {"...": "HASH_REFERENCE"},
  "variables": ["SOURCE_ID", "TARGET_ID"],
  "runtime_logic_family": "missing_expected_delayed_response"
}
```

## Security and scientific boundaries

| Capability | Answer | Enforced by |
|---|---|---|
| arbitrary Python / dynamic eval | NO | closed JSON schema; proposal projection has no code field; downstream runtime is separate |
| file or network access | NO in the DSL | no such operator or field; provider transport is outside rule semantics |
| new sensor | LATER_VERIFIER_CONTROL after schema parse | strings parse structurally, then validity binds the exact approved source/target set |
| arbitrary numeric value | NO | output has hash references only; projected `numeric_literals=[]`; validity rejects literals and mismatched refs |
| change source, target, direction or horizon | LATER_VERIFIER_CONTROL | typed enums/schema plus relation-binding validity checks |
| unapproved operator | NO | the proposal has one fixed runtime-logic family |
| free-form runtime or causal claim | NO | projected `free_text_runtime_logic=null`; prompt and validity prohibit it |
| `no_rule` | controller/outcome state, not DSL code | the three frozen T2 cases have a non-repairable validity cause; the task-specific orchestrator also over-broadly maps explicit failure classes here, which is a recorded HIGH contract mismatch |
| runtime `abstain` | NOT_APPLICABLE here | belongs to later canonical runtime semantics, not construction `no_rule` |

## Lifecycle

`PROPOSED -> PARSED -> TASK-SPECIFIC VALIDITY ADMISSIBLE -> ACCEPTED_PROPOSAL/NO_RULE`

The following are separate later authorities and are not implied by acceptance: canonical Rule v1 materialization, portfolio freeze, COMMON-42 membership and runtime authorization.
