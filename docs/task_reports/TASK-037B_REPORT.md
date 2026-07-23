# TASK-037B Report

Current status: `inner_frozen_outer_pending`.

Commit A defines the dual-arm LSTMAD runner, exact ten-KPI split guards,
generation-only fit and normalization, inner-only threshold selection,
deterministic inference replay, private detector artifacts, generation error
segments, and one-way outer validation.

Commit B freezes twenty checkpoints and normalization artifacts, generation
and inner replay scores, twenty inner operating points, generation and inner
binary predictions, and generation TP/FN/FP/TN segment manifests. Both variants
completed all ten KPI series. No outer value or label was accessed before this
freeze.

`LSTMADalpha` and `LSTMADbeta` remain co-primary provenance-sensitivity arms.
Variant selection, provider or agent activity, rule execution, fusion and
sealed-test access are prohibited.
