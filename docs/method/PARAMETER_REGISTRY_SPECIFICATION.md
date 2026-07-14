# Parameter Registry Specification

## Separation from rule structure

Rules refer to stable IDs such as `PARAM-LAG-001`, `PARAM-TOL-002`,
`PARAM-RATE-003`, `PARAM-RANGE-004`, and `PARAM-DURATION-005`. Numeric values
are stored only in records validated by `schemas/parameter_registry_schema.json`.

Required provenance includes role, value/unit, relation family, variables,
regime, calibration method/split/windows, normal references, support,
stability, confidence interval, uncertainty, dataset/code/calibrator versions,
hash, and approval.

## Approval states

`proposed`, `calibrated`, `rejected`, `unstable`, and `approved` are distinct.
Only `approved` records may be used by an accepted runtime rule.

An LLM may propose a role, dependency, and name. It cannot approve the numeric
value, interval, calibration split, stability result, or uncertainty. The
deterministic calibrator creates the record; deterministic verification checks
provenance and approval.

## Units and compatibility

Units are explicit bounded strings and are checked semantically against node
metadata and relation family. Time roles use compatible time units. Ratio
parameters require compatible or declared dimensionless conversion.
Difference/range/tolerance parameters must match the target dimension.

## Immutability

After a rule is accepted, referenced parameter IDs, versions, values, units,
hashes, dataset version, and calibration split are immutable. Any recalibration
creates a new parameter version and forces rule re-verification.

## Failure policy

Missing, unapproved, unstable, hash-mismatched, test-calibrated, insufficiently
supported, or unit-incompatible parameters reject the candidate. An LLM cannot
override these failures.
