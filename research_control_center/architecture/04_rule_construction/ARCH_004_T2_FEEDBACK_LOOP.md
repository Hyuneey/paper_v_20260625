# ARCH-004 T2 Feedback Loop

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Implemented state machine

1. Render the same frozen construction view used by T1 and each T1-B draw.
2. Make call 1 with the shared strict proposal schema.
3. Parse the response. A refusal, incomplete response or schema failure consumes the call and terminates as `no_rule`.
4. Run deterministic `task039e0_validity_v2` on a parsed proposal.
5. If admissible, record `accepted_proposal` and stop.
6. If rejected, map bounded issue codes to `no_rule`, `retrieve` or `revise`.
7. `retrieve` may re-present one approved slice already in the initial corpus; it does not add scientific evidence and does not itself invoke the model.
8. A follow-up includes the original frozen input, issue codes, affected fields, previous proposal hash and optional approved re-presentation. Chain-of-thought, labels, utility outcomes and new evidence are prohibited.
9. Stop after acceptance, non-repairable rejection, response failure, or the third call. A fourth call and result-dependent budget extension are prohibited.

Limits: maximum three model calls, maximum two follow-up generations, maximum one retrieval action, no scientific generation retries. Transport-only retries are separately governed and do not create a new scientific generation.

## Frozen observation

All 42 T2 relations terminated after call 1. Thirty-nine proposals were admissible. Three proposals used an unsupported variable, a non-repairable issue, and terminated `no_rule`. There were zero revise actions, zero retrieval actions, zero follow-up generations and zero successful feedback recoveries.

## Contract gap

The frozen three `no_rule` outcomes above have a concrete non-repairable validity cause. More broadly, the task-specific orchestrator also collapses response/schema failure, verifier rejection and call-budget exhaustion into `no_rule`. That behavior conflicts with the generic outcome/frozen protocol boundary, where provider failure, invalid structured output, verifier rejection and budget exhaustion are explicit failures rather than semantic `no_rule`. ARCH-004 records this as a HIGH contract mismatch and does not repair production code.

Therefore the loop is an implemented capability, but the frozen cohort does not empirically exercise its feedback edge and cannot demonstrate feedback benefit.
