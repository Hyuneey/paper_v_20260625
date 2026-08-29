# ARCH-000 Legacy and Gap Audit

Independent legacy specialist findings: 27 total; critical 0, high 8, medium 8, low 11. Categories: legacy 6, superseded 1, reference-only 2, design-only 2, implemented-not-used 5, duplicate-entrypoint 5, missing-link 4, governance-coupling 2, possible-dead/unknown 0.

Seven conceptual edges require qualification. Principal risks are the canonical/task verifier split, canonical/synthetic/real runtime layers, task-specific trace hashes instead of the canonical trace in frozen D1, construction recovery lineage, D2 V1 recovery lineage, OUTER blocker-only state, and legacy ARGOS/DSL/verifier/runtime/e2e isolation.
