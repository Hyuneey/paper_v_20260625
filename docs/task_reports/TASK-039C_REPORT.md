# TASK-039C Final Three-Arm Candidate Cohort

Status: `passed_task039c_three_arm_candidate_cohort_freeze`

The frozen primary cohort is the unscored set union of META top20, STAT top20,
and GDN top20. Exact `(source, target)` de-duplication produces 47 candidates.
Serialization follows arm encounter order META, STAT, GDN; it is not a global
scientific ranking.

## Frozen result

- integration execution-code commit: `75a4899ba67e067a88dd363d9bb90554add82cf2`
- META / STAT / GDN top20 counts: 20 / 20 / 20
- META-STAT / META-GDN / STAT-GDN intersections: 11 / 1 / 1
- triple intersection: 0
- final cohort count: 47
- audited preview hash: `81a7b6e0dfffdd6ce1b49799721c3dfcfb484af247a194d87b0602e76ac551ff`
- candidate identity-list hash: `b02304acef7f83c393b73563e486a80fcf32f3ec1997d65051493fe8dbef186c`
- cohort artifact hash: `6d488da608c2804e8cf3a183c4904403eb9904ad858c85beb34b48cb8bd79254`
- overlap artifact hash: `70a9f3db1db86b6341b45d4496f828c99b41a270ebab89e693b4235456f295f4`
- integration receipt hash: `5d53e19542c0334381e0cba1e163f07f89d81092b30af65e706634c08eb1cdb5`
- TASK-039D0 authorization hash: `2820307f52fb02a214c7c7a4e20ec7ef0d04322594756fa572e4be130e9ea860`

## Scientific boundary

META contributes metadata candidate evidence. STAT contributes lagged
change-correlation candidate evidence. GDN contributes learned-graph candidate
evidence. These method-specific values were preserved and were not normalized,
merged, or compared as a common score. All 47 candidates remain relation
confirmation `not_evaluated`; no rule was created.

The low overlap is descriptive, not a failure: the three preregistered methods
expose different candidate sets and create a meaningful common-protocol
comparison opportunity. TASK-039D0 may design that profiling protocol. Real
TASK-039D profiling, HAI access, Rule v2, Agent, detector, runtime, outer, and
sealed execution remain unauthorized.

No HAI feature values, private ledger contents, labels, attacks, or BR2 pair
outcomes were accessed by this integration.
