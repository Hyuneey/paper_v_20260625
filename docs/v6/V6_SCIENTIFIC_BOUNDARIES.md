# V6 Scientific Boundaries

## Validity and Utility

Deterministic validity covers structure, source/target compatibility,
graph/evidence binding, parameter provenance, split compliance, operational
contracts, and claim boundaries.

Rule utility covers normal false-fire, inner attack coverage, detector FN
recovery, added false positives, duplicate firing, and no-op selection.

Attack-label performance must not decide deterministic validity acceptance.

## Evidence

`NormalRelationEvidence` is required for core construction and includes normal
support, response direction, lag/magnitude summaries, stability, operating
regime, matched normal references, and parameter references.

Optional `DetectorErrorContext` may contain authorized development/inner FN or
FP context. It cannot replace or mutate normal evidence.

## Outcomes

- `no_rule`: evidence-insufficient construction termination.
- `no_op`: a valid rule is not selected for application.
- `abstain`: an authorized rule cannot evaluate the runtime window.

Provider failure, invalid JSON, verifier rejection, and budget exhaustion are
explicit failures, not `no_rule`.

## Data, Runtime, and Evaluation

HAI 23.05 is a candidate, not a verified dataset in this task. Raw HAI data is
local-only and untracked. SWaT and WADI remain future external validation.

Core construction is normal-only. Utility is inner-only. Outer selection is
prohibited. Sealed evaluation requires preregistration and explicit approval.

Runtime is LLM-free and executes only accepted, provenance-bound rules.
Explanations bind to observed facts, parameter references, and satisfaction
traces. FN correction is primary; FP correction is supplementary and guarded.
