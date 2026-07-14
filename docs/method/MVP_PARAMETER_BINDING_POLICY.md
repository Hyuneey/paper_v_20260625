# MVP Parameter Binding Policy

## Required Records

The delayed-response MVP requires approved, stable parameter records for lag,
tolerance, persistence duration, minimum support, and severity boundary. Every
record must match the rule/evidence dataset, relation family, variables,
operating regime, calibration split, and normal reference.

`PARAM-SEVERITY-*` with role `severity_boundary` closes the Rule v1 severity
reference. It may be explicitly constructed as a structurally valid record,
but Phase 1 adapters cannot generate it. TASK-032D does not calculate severity.

## Units

The verifier performs only bounded conversion among milliseconds, seconds, and
minutes. Tolerance units must equal the target sensor unit. Support uses a
declared count unit, and severity uses a score/severity unit. General physical
unit algebra is outside the MVP.

## Lag Bindings

Fixed lag uses an approved `response_delay` whose converted value equals both
rule bounds.

An interval may use:

1. `lag_maximum`: the converted value equals the rule maximum, while the rule
   minimum equals both graph and evidence candidate minima; or
2. `response_delay`: the converted confidence interval equals the rule bounds.

In both cases the rule interval must be contained in graph and evidence
candidate ranges. A lone `lag_minimum` is insufficient.

## Window and Support

The approved persistence-duration value must equal the rule window length. An
event-relative window must contain the maximum lag, and enabled persistence
must reference the same duration record. The approved minimum-support value is
checked against evidence support counts.

These checks establish deterministic binding consistency. They do not prove
that a calibration method is statistically optimal or scientifically valid.
