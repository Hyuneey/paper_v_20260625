# `no_rule` Taxonomy

## Intended safe outcome

`no_rule` is a construction absence. It is distinct from runtime `abstain` and governance `no_op`. A non-repairable, evidence-bound proposal issue may terminate T2 safely without fabricating a rule.

## Canonical verifier

`VerifierV1` never emits `no_rule`; it emits `accepted`, `needs_repair`, or `rejected`.

## Task orchestration risk

The frozen protocol says provider/transport failure, verifier rejection and budget exhaustion have separate counters. The task-specific construction orchestration, however, can persist the following as `no_rule`: missing/invalid response, parse/schema failure, rejected proposal, non-repairable validity issue and exhausted generation budget. Consequently a generic persisted `no_rule` is not sufficient to infer “normal evidence was insufficient.” This is a HIGH code-fix candidate; ARCH-005 does not repair it.

| Origin class | Intended distinction | Persisted risk | Scientific interpretation |
|---|---|---|---|
| intentional evidence-bound no rule | valid construction outcome | `no_rule` | interpretable only with reason code |
| non-repairable task validity | rejection with bounded issue | `no_rule` | concrete validity reason, not utility |
| provider/response missing | system/provider failure | may collapse | not scientifically interpretable |
| parse/schema failure | construction failure | may collapse | not evidence insufficiency |
| budget exhaustion | explicit budget outcome | may collapse | not evidence insufficiency |
| canonical verifier rejected | verifier state | no canonical mapping | must remain rejected |
| runtime abstain | incomplete evaluation context | never `no_rule` by contract | runtime-only state |

## Frozen T2 three cases

Sanitized frozen evidence classifies all three anonymously as non-repairable `VALIDITY_UNSUPPORTED_VARIABLE` outcomes. Each is therefore interpretable as a fail-closed task-validity rejection in this cohort. They do not show that the underlying relation lacked normal evidence, and they do not validate the broader conflating implementation.
