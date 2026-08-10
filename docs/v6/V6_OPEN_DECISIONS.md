# V6 Open Decisions

## Production Graph-Ranking Backend

TASK-039P1D resolved the current import and claim boundary: the trainers are
synthetic smoke-only and the masked extractor is a reusable project component,
not a complete GDN model. TASK-039A established HAI source provenance and
TASK-039BR2 selected P1 under the continuous-step feasibility protocol. The
production backend remains open. TASK-039C must choose either a
source-aligned minimal GDN port or a clearly named alternative learned graph
ranker. Only a validated source-aligned backend may be identified as GDN in the
future RQ1 arm.

TASK-039C0 now requires the GDN candidate arm to pass an
`UpstreamGDNFidelityReceipt` before real training. A blocked GDN arm does not
invalidate META or STAT, and no fallback may be renamed GDN. The actual
source-aligned implementation and fidelity evidence remain open in
TASK-039C-GDN.

## Primary Detector

Freeze detector family, training, threshold, development, and selection policy
through a predeclared leakage-safe protocol. ARGOS alpha/beta results cannot
select the v6 detector.

## Rule Severity and Persistence

Retain Rule v1 fields, simplify them through a versioned Rule v2, or defer them
from the HAI MVP only after feasibility, runtime, provenance, and compatibility
evidence. TASK-039P0 creates no Rule v2.

## HAI Process

Official HAI 23.05 provenance is verified. TASK-039B did not select P1 or P3
under the discrete-source gate. TASK-039BR0/BR1 froze the continuous-step route
and its process-neutral policy. TASK-039BR2 executed that policy and selected
P1 because P1 alone passed; P3 remained infeasible. The process decision is
closed for the bounded MVP. Label or test content did not inform it.

## Continuous-Step Rule Semantics

Rule v1 supports a literal `state_changes_to` trigger and remains unchanged.
The continuous-step route therefore requires versioned rule semantics. Open
TASK-039BR1 resolved the experimental trigger, direction, fit-only screening
provenance, support gates, abstention plan, and claim boundary. TASK-039BR2
established process feasibility only; its screening parameters cannot become
runtime parameters. A final Rule v2 schema, canonical parameter artifacts,
verifier implementation, runtime implementation, and operating-regime
calibration remain open. This remains a predefined family, not free-form
trigger invention.

## Evaluation and Sealed Test

Freeze dataset-neutral utility metrics, detector FN endpoints, supplementary
FP/TP/event budgets, process aggregation, outer exposure, and one-time sealed
execution after the foundation and feasibility tasks. No numeric budget is
selected here.
