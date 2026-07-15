# Professor Decision Request

## Context

The ARGOS reference track now includes source alignment, prompt reconstruction,
one-shot real rule capture, static/semantic audit, isolated deterministic rule
execution, a 200-slot generation cohort, inner selection, and one frozen
ten-KPI outer-validation run. The proposed-method track has a deterministic
synthetic contract vertical slice but no real SWaT experiment.

## Decision 1: Is ARGOS reference experimentation sufficient?

Please confirm whether the completed rule-only evidence is sufficient to move
the main effort to the proposed method.

- Continue ARGOS: execute RepairAgent/ReviewAgent studies or broader prompt/
  model comparisons.
- Freeze ARGOS reference work: retain current evidence as the rule-only
  reproduction baseline.

## Decision 2: Run detector and fusion validation first?

Please decide whether detector-only and ARGOS-style detector-rule fusion should
be evaluated before the proposed SWaT experiment.

- Detector/fusion first: directly addresses ARGOS's complementarity claim but
  delays the proposed contribution.
- Defer detector/fusion: advances the proposed relational-rule method sooner,
  while leaving baseline completeness pending.

## Decision 3: Prioritize the SWaT relational-rule experiment?

Please confirm whether the next primary experiment should implement and run the
graph-guided delayed-response MVP on approved official iTrust SWaT data.

This would move from univariate public-KPI rules to the intended multivariate
CPS setting. It requires explicit official-data approval and a separate frozen
split/calibration/evaluation protocol.

## Decision 4: Contribution emphasis

Please indicate the preferred thesis framing:

1. Deterministic verification of generated rule structures and provenance.
2. Anomaly-anchored evidence curation for multivariate relational rules.
3. False-positive-constrained rule composition.
4. Combined system framing integrating all three.

The current evidence supports the combined motivation: unrestricted generation
has operational failure modes, individual rules have narrow coverage, and
unconstrained OR composition can sharply increase false alarms. It does not yet
show which component contributes most on real multivariate CPS data.

## Boundaries for the decision

- Public-KPI validation is not SWaT benchmark evidence.
- Top-3 OR is the best observed trade-off among four frozen arms, not proven
  superior.
- No detector, fusion, RepairAgent, ReviewAgent, or sealed-test result is
  available.
- No causal, final benchmark, or thesis headline claim is requested.
