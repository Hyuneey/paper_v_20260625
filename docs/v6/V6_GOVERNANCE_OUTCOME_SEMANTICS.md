# V6 Governance Outcome Semantics

`RuleGovernanceOutcomeV1` records an inner-only utility decision over an
already accepted rule. It consumes references to the accepted rule, verifier
result, normal guard, inner utility assessment, governance policy, and
optional detector context.

Decisions:

- `selected_rule`: `applied_rule_ref` equals `accepted_rule_ref`.
- `no_op`: `applied_rule_ref` is null and the reason belongs to the frozen
  no-op registry.

`no_op` does not mean invalid rule, verifier rejection, provider failure,
missing rule, `no_rule`, or runtime `abstain`.

Governance requires label-aware inner utility but cannot use outer or sealed
data. P1B records `authority_binding_verified=false`; P1C will bind governance
to canonical accepted-rule and runtime-authority artifacts. No utility
calculation or selection algorithm is implemented here.
