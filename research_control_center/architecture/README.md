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
ARCH-011. Exact next task: `ARCH-001 — Data / Provenance / Split Governance Deep Audit`.
