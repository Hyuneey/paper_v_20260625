# TASK-037C: Frozen Detector-Rule Diagnostic Fusion

Status: `passed_frozen_diagnostic_fusion`.

TASK-037C composes the two frozen TASK-037B LSTMAD variants with all four
frozen TASK-035B rule arms using exact binary maximum and minimum. It reuses
frozen predictions, computes all arms without selection, and preserves the
sealed test.

The implementation commits contain protocols, configuration, DEC-066, and
tests. The result commit contains aggregate fusion reports and status
documentation only. All 320 inner and outer fusion predictions were frozen
before label access, and all 16 arms were retained across all ten KPI series.

This task is diagnostic. It does not implement paper-faithful detector-error-
conditioned rule generation or the full ARGOS Aggregator.
