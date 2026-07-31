# V6 Construction Outcome Semantics

## Arms

- `T0`: deterministic template, zero provider calls, no verifier-feedback
  action.
- `T1`: at most one provider call, no retrieve/revise/feedback.
- `T1_B`: independent budget-matched generation, no retrieve/revise/feedback.
- `T2`: bounded retrieve/revise/verifier-feedback path.

## Terminal States

- `rule_candidate`: a constructed candidate reference, not an accepted rule.
- `no_rule`: normal evidence was insufficient or unstable.
- `provider_error`: provider/transport failure.
- `invalid_output`: response failed the output contract.
- `non_repairable_rejection`: verifier or policy rejection.
- `budget_exhausted`: frozen call or token budget ended construction.

`no_rule` requires a registered evidence-insufficiency reason and a `no_rule`
action. It cannot represent provider error, invalid output, rejection, or
budget exhaustion.

Action history is ordered and unique and contains artifact references,
bounded changed-field names, reason codes, and call indexes. Raw prompts,
responses, time series, and free-text verifier feedback are not artifact
fields.

Construction may return only a candidate and grants neither deterministic
validity nor runtime authority.
