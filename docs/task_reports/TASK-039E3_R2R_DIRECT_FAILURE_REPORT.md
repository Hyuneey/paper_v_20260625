# TASK-039E3-R2R Direct-Number Failure Forensic Audit

Status: `passed_task039e3_r2r_failure_forensic_audit`

The preserved run completed relation 0 T0, T1, all three T1-B calls, and T2 call 1. T2 call 1 produced an admissible `accepted_proposal` outcome. The run then failed while constructing the direct-number request, before a direct-number slot or provider send existed.

The exact relation-0 replay reproduced `TASK039E3PreparationError` with the safe source constant `direct-number calibrated reference leaked`; the never-send count remained zero. The renderer correctly removed the three calibrated bindings and their `numeric_references`, but the same three references remained reachable through `approved_evidence_identities`.

The cause is structural. `project_real_evidence_v1` sets each projected binding's `evidence_identity` equal to its numeric `reference` and derives approved identities from those references. The direct-number renderer does not remove those aliases, while the subsequent guard searches the complete payload for each withheld calibrated reference. This invariant applies to every real-E1 projection without reading all 42 private records.

The synthetic fixture used by the previous offline cohort and audit intentionally used distinct `SYNTHETIC_EVIDENCE_*` identities, so it did not reproduce real-E1 reference/identity aliasing. This explains the historical oracle gap without changing the prior audit record.

The custody chain contains five completed provider records, no HTTP-error records, six proposals, four outcomes, and no direct-number record. These partial outputs are historical custody only. The execution remains `ABORTED_NON_EVALUABLE_PARTIAL_R2R_EXECUTION`; Authorization V2 is consumed and non-reusable, and no resume or rerun is authorized.

Recommended next task: `TASK-039E3-R2R-DIRECT-NUMBER-RENDERING-REMEDIATION`.
