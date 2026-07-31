# V6 Open Decisions

## GDN Fidelity

Decide which torch-backend parts are source-faithful and reusable and how
package import remains usable without unconditional torch. Require pinned
source mapping, synthetic parity, masked Top-K, self-edge, and modern-stack
evidence.

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

## Evaluation and Sealed Test

Freeze dataset-neutral utility metrics, detector FN endpoints, supplementary
FP/TP/event budgets, process aggregation, outer exposure, and one-time sealed
execution after the foundation and feasibility tasks. No numeric budget is
selected here.
