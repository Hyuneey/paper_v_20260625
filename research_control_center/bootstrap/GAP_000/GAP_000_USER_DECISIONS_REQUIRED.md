# GAP-000 User Decisions Required

## USER-DECISION-01 — final scientific execution authority

### A. Canonical RuleV1 / VerifierV1 path
Pros: strongest alignment with the canonical contract narrative.  
Cons: largest migration scope; risks changing evaluated semantics; requires a new runtime and full revalidation.

### B. Officially adopt the V4 COMMON-42 runtime as the final method
Pros: smallest path; matches the frozen executed method.  
Cons: requires narrower thesis wording and leaves canonical VerifierV1 as adjacent architecture rather than the execution authority.

### C. Verified bridge between canonical validity and V4 execution
Pros: preserves frozen V4 execution semantics while proving which canonical claims transfer.  
Cons: medium contract/test work; equivalence may be partial and must fail closed.

Coordinator recommendation: **C if the verified-construction contribution remains central; B is the minimum fallback if the bridge cannot be proven without semantic change.** Do not migrate to A merely for architectural elegance.

## USER-DECISION-02 — conditional contribution policy

Approve the following policy now: keep **Graph-Guided** only if EXP-01 shows stable unique functional contribution, and keep **Agentic** only if EXP-03 exercises feedback and shows a budget-matched benefit. Otherwise narrow the title/contribution without expanding experiments post hoc.

No other current gap requires a research-owner architecture preference. Stronger baseline selection should be a later preregistered experiment-design decision, not a GAP-000 code choice.
