# Metric review — unchanged pre-attack decisions

The pinned official eTaPR authority remains
`af9e7aed35cfd160cbe0d04c8ec4c102502cb677` (MIT).
Keep theta_p 0.5, theta_r 0.1 and delta 0.0, inclusive file-local ranges,
no cross-file merging and no point adjustment.

Independent local-code review did not find a canonical multi-file estimand or
empty-case reporting convention. Existing per-file wrapper equality does not
define either. Preserve the unresolved decisions in the parent
`METRIC_BINDING_DECISION_BRIEF_V2.md`:

1. Multi-file precision/recall weighting and aggregate F1, if aggregate exists.
2. Reference-only, prediction-only and both-empty output and denominator rules.
3. Secondary P1 range/exposure treatment, pending DG-05 scenario authority.

These are future attack-metric gates, not the cause of the current GDN stop.
Official scenario remains primary; P1 eligibility stays design-only; no real
scenario metadata is accessed. No primary pooled Recall or cross-version IID
interpretation is allowed. The 109 existing hypothetical/synthetic cases remain
the conformance target; no new attack fixture is introduced.
