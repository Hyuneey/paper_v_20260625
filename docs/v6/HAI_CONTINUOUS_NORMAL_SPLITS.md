# HAI Continuous Normal Splits

Status: authoritative selected-process normal split manifests created for
`P1` only.

| Role | Files | Split artifact hash |
| --- | --- | --- |
| `normal_candidate_fit` | train1, train2 | `cf02e3474a0ade49aec518a886fef0fb0c405b311d827f593fdc207cfad9ab7a` |
| `normal_relation_calibration` | train3 | `c9e31a99364c0db11f4ad958a93de90ac065661c5171bf8601e2861a5706bba5` |
| `normal_guard` | train4 | `0a09b9171925a24d1955023c41a2b1d9b54682b68ad4c5715943908ff80f0923` |

All splits use `split_before_windowing=true`, a purge gap of 120 samples, no
event IDs, and process scope `P1`. Train4 was bound from its verified public
structural record; its feature values were not opened. No development, inner,
outer, or sealed split was created.
