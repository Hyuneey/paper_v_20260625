# ARCH-001 Label Custody Audit

Verdict: `PASS_WITH_D1_DURABILITY_QUALIFICATION`

- D0: atomic/fsynced/reopened prediction before label plus post-metric byte check.
- D1: self-hashed factory-issued label-blind prediction object before label; public file written after metrics; no explicit persistent state gate.
- D2 V1: durable CombinedPrediction before label plus source/input byte checks.
- D2 V2: durable CombinedPredictionV2 before label plus byte checks.
- OUTER intended controller: labels only after all three predictions freeze.
- OUTER actual recovery: stopped at first feature custody check before content bytes; labels and scientific outputs remained zero.

The D1 finding is an evidence/control gap, not verified label influence.
