# Relational Rule DSL Specification

## Representation

`schemas/rule_dsl_schema.json` defines the only agent-facing rule format. It is
typed JSON, not executable source. Unknown fields are rejected.

The top-level rule binds identity/version/status, subsystem and dataset,
source/target variables, regime, trigger, relation family, expected effect,
lag, window, persistence, parameter/evidence/graph references, output,
severity, abstention, complexity, provenance, review history, and verified hash.

## Trigger registry

Allowed triggers are `state_equals`, `state_changes_to`, `crosses_above`,
`crosses_below`, `enters_range`, `exits_range`, and `sustained_condition`.
Threshold, range, and duration values must be parameter references. A trigger
cannot contain a free-form predicate.

## Lag and window registry

- Lag types: `fixed`, `interval`, `calibrated_distribution`.
- Lag units: milliseconds, seconds, or minutes.
- Window types: `rolling`, `event_relative`, `persistence`, `recovery`.
- Alignments: left, center, right, or trigger-relative.

Numeric fields are runtime-resolved against approved parameter records. The
verifier checks that any structural bounds agree with those records.

## Relation-family registry

Types: `A` actuator/state, `S` continuous/integer sensor, `D` approved derived
state. Support counts are minimum normal matched events unless a later version
records a stricter preregistered policy.

| Family | Types | Required evidence | Lag/window | Parameter roles | Output | Invalid combinations | Minimum support |
|---|---|---|---|---|---|---|---|
| `range` | A/D context -> S | normal variability, baseline | zero/fixed; rolling | range min/max, tolerance | invariant violation | categorical target without numeric encoding | 20 |
| `monotonic_increase` | A/S/D -> S | typical direction/magnitude | fixed/interval; event-relative | tolerance, rate boundary | missing or opposite response | binary target | 15 |
| `monotonic_decrease` | A/S/D -> S | typical direction/magnitude | fixed/interval; event-relative | tolerance, rate boundary | missing or opposite response | binary target | 15 |
| `rate_of_change` | S/D -> S | normal derivative variability | fixed; rolling | rate boundary, tolerance | excessive/unexpected response | irregular sampling without approved resampling | 30 |
| `delayed_response` | A/D -> S/D | state response and typical lag | interval/distribution; event-relative | lag, tolerance, duration | missing/delayed/early response | no trigger transition | 10 triggers and 10 matches |
| `persistence` | A/D -> S/D | state duration and stable response | fixed; persistence | duration, tolerance | premature or missing persistence | duration reference absent | 15 runs |
| `co_movement` | S/D -> S/D | paired normal movement | interval; rolling | tolerance, lag | inconsistent trajectory | identical source/target | 30 paired windows |
| `inverse_co_movement` | S/D -> S/D | paired inverse movement | interval; rolling | tolerance, lag | inconsistent trajectory | identical source/target | 30 paired windows |
| `ratio` | S -> S | stable positive-denominator ratio | fixed; rolling | ratio range, tolerance | invariant violation | denominator near zero or incompatible units | 30 valid windows |
| `difference` | S -> S | normal difference distribution | fixed; rolling | difference range, tolerance | invariant violation | incompatible physical dimensions | 30 windows |
| `state_transition` | A/D -> A/D/S | transition sequence support | interval; event-relative | lag, duration | missing/unexpected transition | continuous source without typed crossing trigger | 10 transitions |
| `conditional_invariant` | A/D context -> S/D | regime-conditioned normal support | fixed/interval; rolling | range/tolerance/support | invariant violation | regime not registered | 30 per regime |
| `trajectory_similarity` | A/S/D -> S | matched normal trajectories | interval; event-relative | trajectory distance, lag | inconsistent trajectory | unequal alignment or unsupported missingness | 20 trajectories |
| `recovery_to_baseline` | A/D/S -> S | baseline and recovery durations | distribution; recovery | baseline, tolerance, duration | delayed/missing recovery | baseline not calibrated | 15 recoveries |

Agents cannot invent a family. Adding one requires a schema-version change,
compatibility rules, calibrator definition, verifier support, runtime operator,
synthetic fixture, tests, and a separate research decision.

## Output semantics

Output types are `binary_anomaly`, `violation_score`, and `abstain`. Violation
directions are missing, excessive, unexpected, delayed, or early response;
inconsistent trajectory; and invariant violation.

Abstention is required for missing variables, regime mismatch, unapproved or
unstable parameters, unsupported missingness, or hash/version mismatch.

## Explicit prohibition

The schema exposes no `python`, `code`, `source_code`, `eval`, `exec`, `import`,
`callable`, `lambda`, `shell`, `command`, or `dynamic_expression` field.
Additional properties are rejected at every executable-semantic boundary.
Mathematical behavior must be represented by a bounded family/operator and
parameter IDs, never a free-form expression string.
