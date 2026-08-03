# V6 Open Decisions

## Production Graph-Ranking Backend

TASK-039P1D resolved the current import and claim boundary: the trainers are
synthetic smoke-only and the masked extractor is a reusable project component,
not a complete GDN model. TASK-039A established HAI source provenance; the
production backend remains open until TASK-039B establishes process
feasibility. TASK-039C must choose either a
source-aligned minimal GDN port or a clearly named alternative learned graph
ranker. Only a validated source-aligned backend may be identified as GDN in the
future RQ1 arm.

## Primary Detector

Freeze detector family, training, threshold, development, and selection policy
through a predeclared leakage-safe protocol. ARGOS alpha/beta results cannot
select the v6 detector.

## Rule Severity and Persistence

Retain Rule v1 fields, simplify them through a versioned Rule v2, or defer them
from the HAI MVP only after feasibility, runtime, provenance, and compatibility
evidence. TASK-039P0 creates no Rule v2.

## HAI Process

Official HAI 23.05 provenance is verified. TASK-039B did not select P1 or P3:
both failed the discrete-source gate. TASK-039BR0 found continuous control
source morphology sufficient to justify a second versioned feasibility
protocol, but did not evaluate a source-target pair. TASK-039BR1 froze the
continuous-step contract and process-neutral policy without real execution.
TASK-039BR2 must now determine feasibility and may select a process only under
that policy. Label or test content cannot inform this decision.

## Continuous-Step Rule Semantics

Rule v1 supports a literal `state_changes_to` trigger and remains unchanged.
The continuous-step route therefore requires versioned rule semantics. Open
TASK-039BR1 resolved the experimental trigger, direction, fit-only screening
provenance, support gates, abstention plan, and claim boundary. A final Rule v2
schema, canonical parameter artifacts, verifier implementation, runtime
implementation, and operating-regime calibration remain open. This remains a
predefined family, not free-form trigger invention.

## Evaluation and Sealed Test

Freeze dataset-neutral utility metrics, detector FN endpoints, supplementary
FP/TP/event budgets, process aggregation, outer exposure, and one-time sealed
execution after the foundation and feasibility tasks. No numeric budget is
selected here.
