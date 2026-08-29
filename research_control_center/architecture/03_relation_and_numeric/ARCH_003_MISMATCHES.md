# ARCH-003 Mismatches and Risks

| ID | Documented or tempting wording | Actual implementation evidence | Type | Scientific impact | Severity | Recommended action |
|---|---|---|---|---|---|---|
| A003-01 | “47 candidates became 23 relations” | There is an evidence-bearing middle stage: 47 pairs / 94 source directions → 25 fit-supported contexts / 45 directions → 23 confirmed contexts / 42 directions. | STATUS_SEMANTIC | Hides selection and confirmation boundaries. | MEDIUM | Always show the full lineage. |
| A003-02 | “Confirmed relation” can read as physical or causal truth | Confirmation means one-way normal train3 transfer under fixed direction, horizon, and parameters. | CLAIM_BOUNDARY | Could overstate the thesis contribution. | HIGH | Use “normal delayed-response relation” and retain non-causal warning. |
| A003-03 | “10-second refractory window” | Actual policy is same-source, file-local single-link clustering of successive gaps up to 10 rows; a chain may span longer end-to-end. | DOCUMENTATION | Changes how duplicated events are understood. | MEDIUM | Say “single-link refractory clustering.” |
| A003-04 | “Seconds” are directly read from timestamps | Profiler requires a timestamp column but operates with row offsets; one-second meaning comes from the frozen sampling contract. | SCHEMA | Timestamp discontinuity is not revalidated locally. | MEDIUM | Document the sampling-contract dependency; review in reproducibility work. |
| A003-05 | Construction numeric authority equals runtime authority | E1 has 42×11 construction-only bindings; frozen D1 uses a new 42×10 runtime registry plus horizon in the descriptor. A focused audit found exact equality for all 420 shared values, but historical authority/reference identities were not restored. | AUTHORITY | Equating value equality with authority identity could misstate what D1 evaluated. | HIGH | State both exact shared-value equivalence and separate authority identity. |
| A003-06 | Runtime registry has no horizon | Horizon is deliberately outside the 10-role private registry and remains bound in each canonical rule descriptor. | AUTHORITY | Counting error could suggest a missing runtime input. | MEDIUM | Show the descriptor branch explicitly. |
| A003-07 | Runtime numeric units are self-describing fields | Units are implicit in closed role names, exact formulas, and validators, not first-class private-record fields. | SCHEMA | Traceable but harder to audit across versions. | MEDIUM | Add documentation now; consider schema change only in a future authorized version. |
| A003-08 | Generic `CalibrationParameterV1` is the frozen D1 registry | Frozen D1 consumes the dedicated normal-only 10-role registry and canonical descriptors. | LEGACY_CURRENT | Can send a future reviewer to the wrong authority path. | LOW | Keep the generic contract as adjacent vocabulary, not execution lineage. |
| A003-09 | Relation thresholds and D0 threshold are one optimization problem | Relation authority controls step/response/window semantics; D0 threshold is PCA-SPE calibration. | METHOD_BOUNDARY | Could contaminate EXP-02 framing. | MEDIUM | Keep EXP-02 relation numeric comparison separate from ARCH-007/D0. |

Counts: 9 total; 0 critical; 2 high; 6 medium; 1 low.

No verified leakage, causal proof, optimality proof, or generalization evidence was found or claimed in this audit.
