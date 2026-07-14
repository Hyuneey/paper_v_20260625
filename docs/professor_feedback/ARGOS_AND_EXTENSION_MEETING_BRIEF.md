# ARGOS Audit to Multivariate CPS Extension

## Why ARGOS was audited first

ARGOS is the closest prior implementation of training-time LLM rule generation
with iterative repair/review and detector-rule combination. Auditing its paper,
source history, prompt path, thresholds, selection, and fusion behavior first
establishes what can be reproduced and what the proposed method must change.
This avoids presenting an unrelated multivariate pipeline as an ARGOS
reproduction.

## What is confirmed

ARGOS has a rule-only generation path and historical detector-correction paths.
DetectionAgent receives labeled training chunks and produces executable Python.
RepairAgent executes and rewrites failed code. ReviewAgent is another LLM agent
that uses performance feedback, not a deterministic verifier. In the pinned
implementation, candidate selection uses validation Event-F1-PA, while test
evaluation also occurs during training iterations. Rule-internal thresholds are
written by the LLM; evaluation utilities separately optimize score thresholds
using labels from the evaluated split.

For detector correction, the FN path uses the union of detector and rule binary
outputs, while the FP path uses their intersection. This supports the
interpretation that ARGOS rules target detector error subsets rather than
universally replacing a mature detector.

## What remains unverified

The captured ARGOS rule has not been executed. Rule-only KPI performance,
RepairAgent and ReviewAgent empirical effects, detector-only performance,
fusion superiority, and paper performance reproduction are not established.
The current evidence is a source and protocol audit, not a benchmark result.

## Limitation in rule control

ARGOS constrains generation mainly through prompts, prior code, execution errors,
and metric feedback. The LLM can still choose variables, thresholds, imports,
and control flow inside unrestricted Python, and an LLM reviewer can rewrite
that code. This limits semantic control, numeric provenance, safety, and exact
reproducibility.

## Proposed extension

The proposed method replaces arbitrary Python with a project-owned typed JSON
DSL. A pre-registered candidate universe and directed attributed graph restrict
source-target pairs. Anomaly-anchored evidence curation binds each candidate to
an event, compatible regime, and deterministically selected normal reference.
A bounded relation-family registry covers delayed response, monotonic behavior,
persistence, co-movement, ratios, differences, state transitions, trajectory
similarity, and recovery.

Numeric values are not approved by an LLM. Deterministic calibrators create
versioned lag, tolerance, duration, rate, baseline, and trajectory parameters
from calibration data with support and uncertainty records. A deterministic
verifier has final authority over schema, variables, graph edges, units,
parameters, split policy, evidence, conflicts, complexity, and claims. A bounded
reviewer may revise only explicitly repairable DSL fields and cannot override a
rejection.

Runtime remains LLM-free. It loads accepted rules, verifies hashes, evaluates
bounded operators, supports abstention, and emits a structured satisfaction
trace. Explanations are rendered from accepted rules and provenance and cannot
introduce causal or root-cause claims.

## Future execution order

1. Complete the isolated ARGOS rule runtime smoke.
2. Reproduce rule-only KPI validation and one-way test behavior.
3. Freeze and run a detector-only baseline.
4. Compare ARGOS FN union and FP intersection without claiming superiority in
   advance.
5. Measure RepairAgent and ReviewAgent effects under frozen inputs.
6. Implement the proposed DSL path first without graph guidance, then add graph
   guidance, deterministic verification, calibration provenance, and bounded
   repair as controlled ablations.
7. Access official iTrust SWaT only after provenance, splits, thresholds, and
   metrics are frozen.

The immediate milestone is an implementation contract with validated synthetic
schemas. It is not the completed method and contains no performance result.
