# TASK-037C: Frozen Detector-Rule Diagnostic Fusion

Status at Commit A: implementation and sixteen-arm matrix frozen; execution
pending.

TASK-037C composes the two frozen TASK-037B LSTMAD variants with all four
frozen TASK-035B rule arms using exact binary maximum and minimum. It reuses
frozen predictions, computes all arms without selection, and preserves the
sealed test.

Commit A contains implementation, protocols, configuration, DEC-066, and
tests. Commit B may contain only aggregate fusion reports and status
documentation.

This task is diagnostic. It does not implement paper-faithful detector-error-
conditioned rule generation or the full ARGOS Aggregator.
