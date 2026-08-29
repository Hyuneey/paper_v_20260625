# Architecture Overview

Scientific authority: `origin/research-v6-thesis-checkpoint` at
`2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## One-line flow

HAI provenance and P1 scope → META, STAT, and GDN candidate discovery → normal
relation evidence → bounded rule construction → deterministic verification and
governance → COMMON-42 → LLM-free D1 runtime → D0 and preregistered D2 pilot
evaluation.

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
- **Runtime and trace:** Accepted rules execute without an LLM and can emit
  satisfaction traces grounded in observed runtime facts.
- **Evaluation:** D0 is the detector arm, D1 is the rule-only arm, and D2 is a
  preregistered combination evaluated in the bounded pilot. The held-out OUTER
  path has no scientific result in the checkpoint.

## Status discipline

Architecture existence is not empirical validation. An implemented component
may still be unexecuted; an audited pilot may still be unreproduced; and a
reproduced result may still be too narrow for a thesis claim. The registry and
dashboard preserve these distinctions component by component.

RCC-001 intentionally provides an overview rather than a complete component
catalog. RCC-002 will populate the detailed architecture inventory from the
pinned scientific source.
