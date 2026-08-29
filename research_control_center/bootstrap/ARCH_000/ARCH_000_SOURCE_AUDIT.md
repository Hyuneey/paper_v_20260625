# ARCH-000 Source Audit

- Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
- Components mapped: 32/32
- Real source or document paths: 32
- Entrypoints: 18
- Verified static edges: 35
- Indirect or unsupported conceptual edges: 10
- Agent source findings: 15 (critical 0, high 6, medium 6, low 3)

The executed construction verifier is `task039e0_validity_v2.verify_prepared_rule_proposal_v2`, not the canonical verifier directly. Frozen D1 uses `execute_real_rule_v1`, not the synthetic evaluator or canonical runtime directly. The frozen C0 universe authority is `CandidateUniversePolicyV1`.
