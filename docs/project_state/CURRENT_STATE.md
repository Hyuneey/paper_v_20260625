# Current project state

## Research in one paragraph

The integrity-audited D0, D1, and D2 V1 results and the D2 V1 negative-result
baseline remain immutable. The single authorized D2 V2 INNER-development
execution has completed under the frozen native-horizon policy. It reused the
exact frozen D0/D1 predictions, source map, and 42-entry native-horizon map;
froze private FusionEvidenceV2 and a 54,000-row label-blind
CombinedPredictionV2 before one label parse; then froze the six preregistered
metrics. No D0/D1/D2 V1 rerun, D0 score access, rule reevaluation, test1
feature access, test2/OUTER access, retry, result-driven change, leakage, or
push occurred.

## D2 V2 INNER execution

- Status: `passed_task039e3_r2r_utility_inner_d2_v2_execution_v1`.
- Scientific state: `D2_V2_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING`.
- Remote state: `LOCAL_ONLY_NOT_PUSHED`.
- Base: `8898c5d4b497931562bc225c287274a2c6512ffe`.
- Execution Implementation Commit A:
  `2bbb3dcaced47c8d15337e45eb0e0b741c1a3ed1`.
- Independent Audit Commit B:
  `b3acf3cbb0b6bcb21548daa319fd37923357b952`.
- Result Freeze Commit C:
  `55d41c543e110a9a6f0f5e2e2671857dba938aaa`.
- Execution version: `TASK039E3_R2R_D2_V2_INNER_EXECUTION_V1`.
- Execution implementation identity:
  `9016e5c8be9fa0e56af6a5d1870617f1937e557b7eabd0afa5b20722e89ded62`.
- Committed authorization / grant:
  `0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45` /
  `9136c3b5432d471181765848619771f5234fae1d1a0c22d60eb584d3b8617392`.
- FusionEvidenceV2 / CombinedPredictionV2:
  `9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb` /
  `31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3`.
- Evidence tokens: `788`; native-horizon corroboration points: `1335`.
- Trigger counts: RULE_RECOVERY `1272`, D0_ONLY `813`, combined `63`, NONE `51852`.
- Point alarms / alarm episodes / rule-recovery episodes: `2148` / `143` / `98`.
- Attack-event Recall / Normal FAR per hour:
  `0.7857142857142857` / `6.915070855955625`.
- D0-missed Attack Recovery / incremental Recall: `0.0` / `0.0`.
- Added Rule-Recovery FAR / incremental Normal FAR:
  `6.4916991708971175` / `6.421137223387365`.
- Metric evidence / public metrics:
  `3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513` /
  `8fabdccc0c9a9b502497aa58163131647303d5e27acefb995a06ca9d43850ba7`.
- Execution/implementation/accounting/readiness:
  `c41957d8e9805afe0e39a0b28b01faaf8fa2ec82d8e4774083f6d7881d5036fc` /
  `fe601aaa195222470e8e746a6c9ba318b338172bc750bff1194bd4164f201ea1` /
  `7059e2b4e54ec53d0b72c072c71487b19efe056ce382357615dc152bf2382aca` /
  `59246da5731bad310c588945326a9f5d44ed9394ed7bf1312086f043566e37bc`.
- Bundle / receipt / report:
  `ded276981ce75ebe5e947bd7a409d14b03208e7e23f1c8e3ddc1cd3070cb915f` /
  `e6f10713d467c4733422f5d4d548035f20b0ebc7e9e10e6ed3d73506375509bf` /
  `e45479ec778414a7e4a3d21b348f898176584abad7f2271baec5f34a21bb6fd6`.
- Static tests: `12 / 12`; independent attacks: `34 / 34` rejected;
  accepted invalid: `0`; semantic differential divergences: `0 / 8`.

## Permanent scientific provenance

D2 V2 remains transparently INNER label-informed development motivated by the
frozen D2 V1 diagnostic. Result magnitude did not alter the frozen policy.
The result is frozen but not yet integrity-audited or interpretation-ready.
D2 V1 remains immutable, while test2 and OUTER remain sealed.

## Exact next task

`TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-V1`

That task must independently audit the frozen result and must not execute D2
V2 again.
