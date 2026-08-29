# ARCH-005 Mismatches

| ID | Tempting/documented wording | Audited implementation | Severity | Disposition |
|---|---|---|---|---|
| A005-M01 | task-specific validity is the canonical verifier | The two implementations validate different objects and only partially overlap | HIGH | terminology corrected; code bridge not present |
| A005-M02 | accepted proposal is a canonical Rule | No lossless proposal-to-`DelayedResponseRuleV1` bridge is tracked | HIGH | REQUIRES_CODE_FIX or explicit future bridge |
| A005-M03 | VerifierV1 governed COMMON-42 | COMMON-42 depends on task validity plus executable-equivalence/V4 replay; VerifierV1 invocation is not proven | HIGH | current docs corrected |
| A005-M04 | V4 `CanonicalRuleDescriptorV4` equals canonical Rule v1 | It is a task-specific runtime descriptor | HIGH | maintain explicit type qualifier |
| A005-M05 | verifier acceptance grants runtime execution | Both verifier systems leave runtime unauthorized | HIGH | separate authorization documented |
| A005-M06 | canonical `runtime_authority.py` governed frozen D1 | D1 used V4/evaluator/committed INNER grant | HIGH | DEFER canonical runtime comparison to ARCH-006 |
| A005-M07 | COMMON-42 is T2/Agentic output | COMMON means T0/T1/T1-B shared executable projection; T2 excluded | HIGH | terminology corrected |
| A005-M08 | D1 is LLM Rule-only | D1 loads an arm-deduplicated V4 descriptor portfolio without provider artifacts | MEDIUM | use COMMON-42 Verified Relational Rule-only |
| A005-M09 | every `no_rule` is evidence insufficiency | orchestration can collapse response/parser/rejection/budget failures | HIGH | REQUIRES_CODE_FIX; frozen three remain interpretable |
| A005-M10 | verifier stage 16 proves general subsumption | implementation checks exact structural projection duplicates | MEDIUM | stage description narrowed |
| A005-M11 | one numeric authority identity persists end-to-end | construction/runtime shared values match but identities are separately rebound | HIGH | resolved by V4 trace plus ARCH-003 qualification |

Counts: 11 total; 0 critical; 9 high; 2 medium; 0 low.
