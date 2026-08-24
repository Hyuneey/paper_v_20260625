# End-to-end architecture audit

| Transition | Classification | Remote evidence and finding |
|---|---|---|
| HAI provenance/contracts → split governance | CONNECTED_AND_USED | `paperworks.data.hai_provenance_v1`, v2 contracts/splits, and frozen HAI manifests bind the approved edition and split roles. |
| split governance → P1 process freeze | CONNECTED_AND_USED | BR2 freezes P1 Boiler under the continuous-step feasibility policy. |
| P1 → META/STAT/GDN candidate discovery | CONNECTED_AND_USED | One 144-pair universe feeds three separated discovery arms. |
| META/STAT/GDN → 47-pair cohort | CONNECTED_AND_USED | Candidate integration is an unscored provenance-preserving union; the upstream-aligned GDN arm is candidate evidence, not causality. |
| cohort → normal relation profiling | CONNECTED_AND_USED | Train1/2 fit consumes the frozen cohort under `task039d0_relation_profiling_protocol.json`. |
| fit → train3 confirmation → 42 relations | CONNECTED_AND_USED | One-way normal confirmation yields 23 pairs and 42 directed relations. |
| relations → normal evidence/numeric authority | CONNECTED_AND_USED | Normal evidence and 420 private numeric bindings are separated from public identities. |
| evidence → T0/T1/T1-B/T2 construction | CONNECTED_AND_USED | Deterministic and bounded provider-assisted arms use the same closed contracts; provider-dependent arms are research workflows. |
| constructed rules → deterministic verifier | CONNECTED_AND_USED | `contracts.verifier_v1` performs closed, staged structural/evidence/parameter/claim checks. |
| verifier → COMMON-42 | CONNECTED_AND_USED | Accepted relations/rules are frozen into the common 42-rule utility portfolio. |
| COMMON-42 → D1 runtime/trace | CONNECTED_AND_USED | The D1 evaluator is LLM-free and emits rule decisions and satisfaction traces. |
| normal data → D0 PCA-SPE | CONNECTED_AND_USED | Frozen normal-only training/calibration produces the reference detector. |
| D0 + D1 → D2 V1/V2 | CONNECTED_AND_USED | V1 uses same-second two-source corroboration; V2 uses causal per-rule native-horizon persistence. |
| predictions → event/episode metrics | CONNECTED_AND_USED | Label-blind predictions freeze before label parsing; event recall and normal FAR policies are explicit. |
| frozen metrics → professor package | CONNECTED_AND_USED | Submission tables match all four frozen arms and preserve the INNER-only claim boundary. |

Historical ARGOS and old DSL/runtime/e2e paths remain
`CONNECTED_BUT_HISTORICAL`. TSFM, ARTIST-style segment selection, a stronger
detector comparison, human explanation evaluation, and a scientific OUTER
result are `MISSING` from the current empirical package. Generalized decrease
and multi-stage rule families are `PARTIAL`.
