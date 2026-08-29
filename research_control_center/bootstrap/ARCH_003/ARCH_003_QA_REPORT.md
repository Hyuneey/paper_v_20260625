# ARCH-003 Independent QA Report

Verdict: **PASS**

All 18 required questions were satisfactory:

1. Candidate and confirmed relation are distinct.
2. Source-event extraction is accurate.
3. Target-response calculation is accurate.
4. All five horizons are source-supported.
5. Support definition and gates are source-supported.
6. Consistency definition and gates are source-supported.
7. Robust-effect definition and gates are source-supported.
8. train1/train2 roles are accurate.
9. train3 is constrained confirmation, not a new search.
10. Alternate-horizon search after confirmation failure is absent.
11. The 47→94→25/45→23/42 counts are frozen-artifact-supported.
12. Runtime-relevant values and horizon are traceable.
13. Construction and runtime authorities are distinguished.
14. Their exact binding and shared-value equivalence are accurately represented.
15. D0 PCA-SPE threshold is clearly separate.
16. STAT candidate ranking is clearly separate from event profiling.
17. Causal and optimality claims are avoided.
18. No scientific execution occurred.

The reviewer independently checked the focused numeric artifact: 420 records checked, 420 exact E1 numeric matches, and zero value, relation, or role mismatches. Official text correctly preserves separate authority and reference identities.

Validation: registry PASS; RCC tests 61/61 PASS; privacy exposures 0. There were no scientific executions, test2 accesses, private numeric reads, scientific-source changes, frozen-artifact changes, or pushes.

Non-blocking notes: row-offset “seconds” rely on the frozen one-second sampling contract (MEDIUM documentation/reproducibility concern); duplicate representation of seven window constants remains controlled by exact validators (LOW maintainability concern).

Detailed QA evidence: `agents/agent_e_qa.json`.
