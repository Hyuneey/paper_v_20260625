# ARCH-004 Population Report

Status: PASS.

The audit statically traced frozen normal-only E1 evidence through the E3 construction view, closed proposal schema, parser, task-specific validity, arm outcomes and public result analysis. It made zero provider calls and zero scientific executions.

Key result: T0/T1/T1-B/T2 accepted counts are relation-level `accepted_proposal` outcomes (42/42, 42/42, 42/42, 39/42), not canonical Rule v1, portfolio, runtime-authority or detection counts. T2 implemented a bounded feedback controller but observed zero revise/retrieve/follow-up actions.

One HIGH contract gap remains: the task-specific orchestrator can collapse response/schema failure, verifier rejection and budget exhaustion into `no_rule`, whereas the generic/frozen protocol keeps those as explicit failures. The three frozen T2 no-rule cases themselves remain specifically bound to non-repairable validity issues.

Independent QA answered all 18 required questions satisfactorily after three terminology/contract corrections. Registry refresh, 66 RCC tests, compile and privacy checks passed.

Exact next task: `ARCH-005 — Deterministic Verifier / COMMON-42 Deep Audit`.
