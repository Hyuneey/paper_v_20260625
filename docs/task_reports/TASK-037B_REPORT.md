# TASK-037B Report

Current status: `implementation_and_execution_protocol_frozen`.

Commit A defines the dual-arm LSTMAD runner, exact ten-KPI split guards,
generation-only fit and normalization, inner-only threshold selection,
deterministic inference replay, private detector artifacts, generation error
segments, and one-way outer validation. No real detector unit has run at this
commit boundary.

`LSTMADalpha` and `LSTMADbeta` remain co-primary provenance-sensitivity arms.
Variant selection, provider or agent activity, rule execution, fusion and
sealed-test access are prohibited.
