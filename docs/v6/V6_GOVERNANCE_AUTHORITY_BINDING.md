# V6 Governance Authority Binding

Construction and governance remain separate from deterministic validity.

## Construction Candidate

`ConstructionCandidateBindingReceiptV1` binds only a
`rule_candidate` construction outcome to the exact Rule v1 transport hash and
normal-evidence context. It rejects `no_rule`, provider failure, invalid
output, non-repairable rejection, and budget exhaustion.

The receipt grants no validity or runtime authority.

## Governance

`GovernanceAuthorityBindingReceiptV1` binds an existing P1B governance outcome
to:

- one accepted Rule v1;
- one accepted verifier result;
- one canonical v6 collection;
- the referenced normal-guard assessment;
- the referenced inner-utility assessment;
- the frozen governance policy.

It does not compute utility or rerun validity. `selected_rule` is deployable
only after a separate runtime receipt. `no_op` is non-deployable and cannot
create runtime authority. Outer and sealed governance evidence fail closed.
