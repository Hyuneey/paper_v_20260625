# V6 Open Decisions

## Production Graph-Ranking Backend

TASK-039P1D resolved the current import and claim boundary: the trainers are
synthetic smoke-only and the masked extractor is a reusable project component,
not a complete GDN model. The production backend remains open until TASK-039A/B
establish HAI schema and process feasibility. TASK-039C must choose either a
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

Select exactly one process only after official HAI 23.05 provenance, feature
typing, normal support, delayed-response evidence, and split viability.
TASK-039A cannot select P1 or P3 and cannot use label or test content for this
decision.

## Evaluation and Sealed Test

Freeze dataset-neutral utility metrics, detector FN endpoints, supplementary
FP/TP/event budgets, process aggregation, outer exposure, and one-time sealed
execution after the foundation and feasibility tasks. No numeric budget is
selected here.
