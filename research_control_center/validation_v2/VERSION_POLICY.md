# VALIDATION V2 Version Policy

## PILOT V1

- Scientific authority: `origin/research-v6-thesis-checkpoint`
- Commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
- Status: immutable, historically interpretable with existing qualifications
- Existing source files, artifacts, predictions, reports, and hashes must not be
  modified, deleted, migrated, or overwritten.

## VALIDATION V2

- Integration branch: `validation-v2`
- Base RCC commit: `4fcc4ec501711a3f3a3335183ecd5f80fc4b39bd`
- New method, configuration, authority, prediction, experiment, artifact, and
  report identities are mandatory.
- Existing PILOT V1 paths may be imported but not edited. Prospective code must
  live in new V2 modules and schemas.
- `test1` is development-only. A future held-out study requires DG-05.

## Final execution authority

`DEC-020 = APPROVED_FORMAL_V4`; `DG-01 = RESOLVED_BY_USER`.

The research owner selected Formal V4 adoption for VALIDATION V2. The
scientific execution authority is the versioned `CanonicalRuleDescriptorV4`
representation plus V4 task validity, replay/conformance, Utility V4 numeric
binding, portfolio freeze, runtime authorization, durable prediction custody,
and versioned metric/result-integrity controls.

Canonical `RuleV1` and `VerifierV1` remain implemented adjacent rule-validity
components. They did not directly verify or authorize the V4 runtime. The
canonical-to-V4 bridge is `NOT_SELECTED` and
`NOT_REQUIRED_FOR_MINIMUM_THESIS_PATH`.

> VALIDATION V2 formally adopts the versioned V4 relational-rule descriptor
> and its deterministic validity, numeric binding, replay, portfolio-freeze,
> and runtime-authorization controls as the scientific execution authority.

This authority controls executable eligibility and integrity. It does not
prove scientific utility, causal direction, physical truth, generalization,
or explanation usefulness.

## Baseline decision

The additional detector is a normal-only `IsolationForest` baseline. It is
described as an additional nonlinear multivariate baseline, not as a temporal
SOTA detector or as superior to PCA-SPE before evaluation.
