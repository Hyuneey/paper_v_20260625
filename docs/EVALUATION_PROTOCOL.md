# Restricted Evaluation Protocol

TASK-014 implements evaluation harness code only. It does not run a final SWaT
benchmark and does not approve final test access.

## Current Scope

Approved:

- evaluation report structure,
- metric interfaces,
- PA-free primary metric reporting,
- supplementary point-adjusted metric reporting when clearly labeled,
- sealed-test access guards,
- config-freezing checks,
- provenance and manifest checks,
- synthetic or toy fixture tests.

Not approved:

- opening sealed final test data,
- running final SWaT benchmark evaluation,
- using unverified local SWaT files for final claims,
- tuning thresholds or K using final test labels,
- reporting point-adjusted metrics as primary,
- detector fusion as a headline result,
- real LLM provider calls,
- benchmark or thesis-result claims.

## Primary Metrics

Primary metrics are PA-free:

- `pa_free_precision`,
- `pa_free_recall`,
- `pa_free_f1`,
- `auroc`,
- `auprc`,
- range or event metrics when implemented and pre-registered.

Point-adjusted metrics must not be used for model selection, threshold
selection, rule selection, K selection, or headline claims.

## Supplementary Metrics

Point-adjusted metrics may be reported only as supplementary and must be named
with the `point_adjusted_` prefix.

## Sealed-Test Access Guard

Final test access requires all of the following:

- DEC-007 resolved,
- explicit final-test access approval,
- frozen thresholds,
- frozen candidate K,
- frozen prompt/planner configuration,
- frozen fusion weights if fusion is evaluated,
- artifact provenance present,
- one-way execution log plan.

If any condition is missing, final test access must fail before metrics are
computed.

## DEC-007 Requirements Before Final SWaT Evaluation

Resolve and record:

- official SWaT provenance,
- terms-of-use status,
- exact dataset edition/version,
- file hashes,
- final split protocol,
- sealed test access policy,
- primary and supplementary metric list,
- allowed artifacts for Git tracking.

Until DEC-007 is resolved, evaluation outputs are harness or synthetic-fixture
artifacts only and must not be described as final SWaT performance.

## Report Requirements

Each evaluation report must include:

- `schema_version`,
- `artifact_type`,
- dataset and split role,
- primary metrics,
- supplementary metrics,
- protocol hash,
- config hash,
- artifact provenance,
- sealed-test audit,
- manifest checks,
- limitations,
- code commit,
- creation timestamp.

Reports must not contain raw SWaT rows, windows, full time-series sequences, or
downloadable derived samples.
