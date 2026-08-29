# ARCH-002 Candidate Union Audit

Verdict: `VERIFIED_UNSCORED_PROVENANCE_PRESERVING_SET_UNION`.

Integration consumes exact META, STAT, and GDN Top-20 prefixes. Duplicate `(source,target)` identities collapse while arm ranks and method provenance remain. No score normalization, merged score, or global scientific rank is created; stable META→STAT→GDN serialization is not ranking.

Exact decomposition: META-only 8, STAT-only 8, GDN-only 18, exactly two arms 13, all three 0, total 47. Relation confirmation had not run within the discovery cohort. Scientific executions and test2 accesses: 0.
