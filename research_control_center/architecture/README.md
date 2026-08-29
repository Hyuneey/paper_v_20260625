# Architecture Overview

Scientific authority: `origin/research-v6-thesis-checkpoint` at
`2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Current verified overview

ARCH-000 is the first source-, entrypoint-, artifact-, and frozen-result-grounded map:

- [Korean architecture report](00_overview/ARCH_000_REPORT.md)
- [Source map](00_overview/ARCH_000_SOURCE_MAP.csv)
- [Entrypoint map](00_overview/ARCH_000_ENTRYPOINT_MAP.csv)
- [Verified and unknown dataflow edges](00_overview/ARCH_000_DATAFLOW.csv)
- [Artifact lineage](00_overview/ARCH_000_ARTIFACT_LINEAGE.csv)
- [D0/D1/D2 result lineage](00_overview/ARCH_000_RESULT_LINEAGE.md)
- [Core / governance classification](00_overview/ARCH_000_CORE_GOVERNANCE_MAP.md)
- [Legacy and gap index](00_overview/ARCH_000_LEGACY_AND_GAPS.md)
- [Mismatch register](00_overview/ARCH_000_MISMATCHES.md)
- [Deep-review index](00_overview/DEEP_REVIEW_INDEX.md)

A dotted edge or `verified=UNKNOWN` means the documented relationship was not
established as a direct source edge.

## One-line flow

HAI provenance and P1 scope → frozen role universe → META, STAT, and GDN →
unscored candidate union → normal relation profiling → construction evidence →
T0/T1/T1-B/T2 → task verifier. T0/T1/T1-B equivalence then binds COMMON-42;
private runtime numeric authority drives the real D1 bridge. D0 is parallel,
and frozen D0 plus D1 predictions feed preregistered D2 policies.

## How to read the flow

- **Data and scope:** Provenance and split governance establish which public
  metadata and private scientific inputs a stage may use.
- **Candidate discovery:** META, STAT, and GDN produce bounded candidate
  relations. A GDN edge is candidate evidence, not a causal claim.
- **Evidence and construction:** Normal-only relation evidence and numeric
  authorities constrain rule construction. Provider-assisted arms may propose
  bounded structures; they do not approve themselves or choose uncontrolled
  numeric parameters.
- **Verification and governance:** Deterministic checks establish rule validity;
  label-aware utility remains a separate layer.
- **Runtime and trace:** Accepted rules execute without an LLM. The frozen D1
  bridge records task-specific trace hashes; a direct `RuntimeTraceV1` link and
  frozen explanation artifact were not found.
- **Evaluation:** D0 is the detector arm, D1 is the rule-only arm, and D2 is a
  preregistered combination evaluated in the bounded pilot. The held-out OUTER
  path has no scientific result in the checkpoint.

## Status discipline

Architecture existence is not empirical validation. An implemented component
may still be unexecuted; an audited pilot may still be unreproduced; and a
reproduced result may still be too narrow for a thesis claim. The registry and
dashboard preserve these distinctions component by component.

ARCH-000 maps all 32 components at overview level. Function-level dependencies,
ownership, and semantic-equivalence questions remain deferred to ARCH-001 through
ARCH-011.

## Completed deep audit

ARCH-001 verifies the data foundation without reading scientific payloads:

- [Korean data and split report](01_data_and_splits/ARCH_001_REPORT.md)
- [Leakage matrix](01_data_and_splits/ARCH_001_LEAKAGE_MATRIX.csv)
- [Label-access timeline](01_data_and_splits/ARCH_001_LABEL_ACCESS_TIMELINE.md)
- [Input contracts](01_data_and_splits/ARCH_001_INPUT_CONTRACTS.csv)
- [Function catalog](01_data_and_splits/ARCH_001_FUNCTION_CATALOG.csv)
- [Split flow](01_data_and_splits/ARCH_001_SPLIT_FLOW.mmd)
- [Mismatch register](01_data_and_splits/ARCH_001_MISMATCHES.md)

Its conclusion is `NO VERIFIED LEAKAGE FOUND`, with explicit qualifications:
D1 lacks a durable prediction-file-before-label gate, D2 V2 is test1-informed,
split enforcement is distributed, and train3 has a documented dual role.

## Completed candidate-discovery audit

ARCH-002 verifies the three proposal arms and their 47-pair handoff:

- [Korean report](02_candidate_discovery/ARCH_002_REPORT.md)
- [Arm comparison](02_candidate_discovery/ARCH_002_ARM_COMPARISON.csv)
- [Candidate provenance](02_candidate_discovery/ARCH_002_CANDIDATE_PROVENANCE.csv)
- [Function catalog](02_candidate_discovery/ARCH_002_FUNCTION_CATALOG.csv)
- [I/O contracts](02_candidate_discovery/ARCH_002_IO_CONTRACTS.csv)
- [Discovery flow](02_candidate_discovery/ARCH_002_DISCOVERY_FLOW.mmd)
- [Professor-facing GDN answer](02_candidate_discovery/ARCH_002_GDN_PROFESSOR_ANSWER.md)
- [Mismatch register](02_candidate_discovery/ARCH_002_MISMATCHES.md)

The GDN candidate authority is the node-embedding cosine learned graph. Graph
attention is internal message passing, not candidate-ranking evidence; post-hoc
XAI is absent. Candidate discovery remains proposal, not confirmation or causality.

## Completed relation and numeric-authority audit

- [Korean report](03_relation_and_numeric/ARCH_003_REPORT.md)
- [Relation schema](03_relation_and_numeric/ARCH_003_RELATION_SCHEMA.md)
- [Metric definitions](03_relation_and_numeric/ARCH_003_METRIC_DEFINITIONS.md)
- [Sanitized relation lineage](03_relation_and_numeric/ARCH_003_RELATION_LINEAGE.csv)
- [Numeric authority catalog](03_relation_and_numeric/ARCH_003_NUMERIC_AUTHORITY.csv)
- [Construction/runtime authority](03_relation_and_numeric/ARCH_003_CONSTRUCTION_RUNTIME_AUTHORITY.md)
- [Function catalog](03_relation_and_numeric/ARCH_003_FUNCTION_CATALOG.csv)
- [I/O contracts](03_relation_and_numeric/ARCH_003_IO_CONTRACTS.csv)
- [Relation flow](03_relation_and_numeric/ARCH_003_RELATION_FLOW.mmd)
- [Mismatch register](03_relation_and_numeric/ARCH_003_MISMATCHES.md)

## Completed rule-construction audit

- [Korean report](04_rule_construction/ARCH_004_REPORT.md)
- [Evidence Pack schema](04_rule_construction/ARCH_004_EVIDENCE_PACK_SCHEMA.md)
- [Evidence lineage](04_rule_construction/ARCH_004_EVIDENCE_LINEAGE.csv)
- [Rule DSL boundary](04_rule_construction/ARCH_004_RULE_DSL.md)
- [Arm outcomes](04_rule_construction/ARCH_004_ARM_OUTCOMES.csv)
- [T2 feedback loop](04_rule_construction/ARCH_004_T2_FEEDBACK_LOOP.md)
- [Agentic claim boundary](04_rule_construction/ARCH_004_AGENTIC_CLAIM_BOUNDARY.md)
- [Function catalog](04_rule_construction/ARCH_004_FUNCTION_CATALOG.csv)
- [I/O contracts](04_rule_construction/ARCH_004_IO_CONTRACTS.csv)
- [Construction flow](04_rule_construction/ARCH_004_RULE_CONSTRUCTION_FLOW.mmd)
- [Mismatch register](04_rule_construction/ARCH_004_MISMATCHES.md)

`accepted_proposal` is task-specific validity admissibility. It is not canonical
Rule v1 materialization, COMMON-42 membership, runtime authority, or detection
performance. T2 has a bounded feedback capability, but the frozen cohort used
zero revise/retrieve actions.

## Completed verifier / COMMON-42 audit

- [Korean report](05_verifier_common42/ARCH_005_REPORT.md)
- [Rule lifecycle](05_verifier_common42/ARCH_005_RULE_LIFECYCLE.md)
- [Canonical Rule schema](05_verifier_common42/ARCH_005_CANONICAL_RULE_SCHEMA.md)
- [20 verifier stages](05_verifier_common42/ARCH_005_VERIFIER_STAGES.csv)
- [Task/canonical matrix](05_verifier_common42/ARCH_005_VALIDITY_EQUIVALENCE.csv)
- [COMMON-42 definition](05_verifier_common42/ARCH_005_COMMON42.md)
- [Arm/portfolio mapping](05_verifier_common42/ARCH_005_ARM_PORTFOLIO_MAPPING.csv)
- [Runtime authorization](05_verifier_common42/ARCH_005_RUNTIME_AUTHORIZATION.md)
- [No-rule taxonomy](05_verifier_common42/ARCH_005_NO_RULE_TAXONOMY.md)
- [Prior HIGH-risk disposition](05_verifier_common42/ARCH_005_HIGH_RISK_DISPOSITION.md)
- [Mismatch register](05_verifier_common42/ARCH_005_MISMATCHES.md)

The general canonical RuleV1/verifier/runtime-authority plane and the frozen D1
V4/evaluator/committed-grant plane are separate. COMMON-42 is the 42 executable
projections shared by T0/T1/T1-B; T2 is excluded. Preferred D1 terminology is
`COMMON-42 Verified Relational Rule-only`, with verified limited to contract,
provenance, authority and integrity.

## Completed runtime / trace audit

- [Korean report](06_runtime_trace_explanation/ARCH_006_REPORT.md)
- [Runtime state machine](06_runtime_trace_explanation/ARCH_006_RUNTIME_STATE_MACHINE.md)
- [D1 freeze boundary](06_runtime_trace_explanation/ARCH_006_D1_FREEZE_BOUNDARY.md)
- [Trace schema](06_runtime_trace_explanation/ARCH_006_TRACE_SCHEMA.csv)

## Completed D0 PCA-SPE audit

- [Korean report](07_d0_detector/ARCH_007_REPORT.md)
- [D0 role](07_d0_detector/ARCH_007_D0_ROLE.md)
- [Feature contract](07_d0_detector/ARCH_007_FEATURE_CONTRACT.md)
- [SPE definition](07_d0_detector/ARCH_007_SPE_DEFINITION.md)
- [Durable prediction freeze](07_d0_detector/ARCH_007_FREEZE_BOUNDARY.md)
- [Output levels](07_d0_detector/ARCH_007_OUTPUT_LEVELS.md)
- [D0 flow](07_d0_detector/ARCH_007_D0_FLOW.mmd)
- [Mismatch register](07_d0_detector/ARCH_007_MISMATCHES.md)

D0 is a 37-feature, normal-only, custom NumPy PCA-SPE reference detector. The
0.95 explained-variance policy selected `k=10`; train3 supplies a no-interpolation
q=.999 order statistic and alarms use strict `score > threshold`. Its frozen
prediction was durably persisted before labels. Current results remain 14-event
pilot evidence and do not support a SOTA or generalization claim.

## Completed D1 Rule-only evaluation audit

- [Korean report](08_d1_rule_only/ARCH_008_REPORT.md)
- [Evaluated object](08_d1_rule_only/ARCH_008_D1_EVALUATED_OBJECT.md)
- [Output levels](08_d1_rule_only/ARCH_008_OUTPUT_LEVELS.md)
- [Attack-event evaluation](08_d1_rule_only/ARCH_008_ATTACK_EVENT_EVALUATION.md)
- [Normal false alarms](08_d1_rule_only/ARCH_008_NORMAL_FALSE_ALARMS.md)
- [D0/D1 overlap](08_d1_rule_only/ARCH_008_D0_D1_OVERLAP.csv)
- [Complementarity boundary](08_d1_rule_only/ARCH_008_COMPLEMENTARITY_BOUNDARY.md)
- [Rule-only utility](08_d1_rule_only/ARCH_008_RULE_ONLY_UTILITY.md)
- [Claim matrix](08_d1_rule_only/ARCH_008_CLAIM_MATRIX.csv)
- [Mismatch register](08_d1_rule_only/ARCH_008_MISMATCHES.md)

D1 produced a 13/14 attack-event response and responded to all three D0-missed
events in the frozen INNER pilot, but also produced 574 normal false episodes
and 40.50255787059723 FAR/hour. This is a response-diversity pilot signal, not
validated complementarity or operational utility. D1 remains COMMON-42 Verified
Relational Rule-only, not T2 Agentic Rule-only.

Exact next task: `ARCH-009 — D2 Detector + Rule Fusion Deep Audit`.
