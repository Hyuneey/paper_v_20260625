# Added-alarm taxonomy

| Category | Meaning | V1 trigger | V2 trigger |
|---|---|---|---|
| D0 retained | D0 was already alarming | `D0_ONLY` | `D0_ONLY` |
| Both support | D0 alarm and policy-admitted D1 evidence coincide | `D0_AND_RULE_CORROBORATION` | `D0_AND_RULE_CORROBORATION_NATIVE_HORIZON` |
| D2-added | D0 is false and D1 evidence passes the policy gate | `RULE_RECOVERY` | `RULE_RECOVERY_NATIVE_HORIZON` |
| No alarm | neither input path qualifies | `NONE` | `NONE` |
| System failure | invalid authority/schema/hash or persistence failure | fail closed; no scientific normal prediction | fail closed; no scientific normal prediction |

Frozen aggregates show three V1 rule-recovery points/episodes and 1,272 V2
rule-recovery points yielding 98 V2 rule-recovery episodes. Existing metric
evidence reports no D0-missed attack-event recovery for either policy. These
counts must not be interpreted as useful recoveries merely because the trigger
class contains the word `RECOVERY`.
