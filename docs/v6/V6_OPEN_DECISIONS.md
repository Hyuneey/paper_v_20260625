# V6 Open Decisions

## Production Graph-Ranking Backend

TASK-039P1D resolved the current import and claim boundary: the trainers are
synthetic smoke-only and the masked extractor is a reusable project component,
not a complete GDN model. TASK-039A established HAI source provenance; the
production backend remains open. TASK-039B did not establish a feasible
single-process source population, so TASK-039C is not authorized to choose or
train a backend. After a new process/source decision, a future task may choose
either a source-aligned minimal GDN port or a clearly named alternative learned
graph ranker. Only a validated source-aligned backend may be identified as GDN
in the future RQ1 arm.

## Primary Detector

Freeze detector family, training, threshold, development, and selection policy
through a predeclared leakage-safe protocol. ARGOS alpha/beta results cannot
select the v6 detector.

## Rule Severity and Persistence

Retain Rule v1 fields, simplify them through a versioned Rule v2, or defer them
from the HAI MVP only after feasibility, runtime, provenance, and compatibility
evidence. TASK-039P0 creates no Rule v2.

## HAI Process

Official HAI 23.05 provenance is verified. TASK-039B evaluated P1/P3 using
normal data only and found zero eligible reviewed, nonconstant binary/discrete
sources in both processes. No process was selected. A new preregistered task
must decide whether to revise process scope, source semantics, or the first
relation family without rewriting the frozen blocked result. Label or test
content cannot inform that decision.

## Evaluation and Sealed Test

Freeze dataset-neutral utility metrics, detector FN endpoints, supplementary
FP/TP/event budgets, process aggregation, outer exposure, and one-time sealed
execution after the foundation and feasibility tasks. No numeric budget is
selected here.
