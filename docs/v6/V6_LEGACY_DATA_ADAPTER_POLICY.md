# V6 Legacy Data Adapter Policy

## Purpose

The v2 adapters preserve historical v1 artifacts without silently assigning
new scientific meaning. Every result has one terminal status:

- `created`;
- `pending_context`;
- `unsupported_source`;
- `invalid_source`.

Every result records the source hash, requested target role, target hash when
created, information loss, and `sealed_access_granted=false`.

## Role Mapping

| Legacy role | V2 mapping policy |
|---|---|
| `train_normal` | `normal_candidate_fit` only when explicitly requested |
| `calibration_normal` | `normal_relation_calibration` only when explicitly requested |
| `validation` | Requires explicit `development`, `inner_utility`, or `outer_validation` context |
| `test` | Requires explicit sealed policy context and is rejected when previously exposed |

No mapping infers process scope. Split creation remains pending until an
explicit process scope is supplied.

## Information Loss

Legacy contracts do not consistently record:

- per-file compression, time range, process IDs, or label availability;
- timestamp format and timezone;
- source sampling interval and aggregation method;
- event IDs and v6 creation policy.

Adapters report these losses rather than inventing values. Dataset and view
contracts retain explicit unknown or unverified states.

## Sealed Boundary

Even a preregistered legacy test mapping receives
`sealed_access_status=approval_required`. The adapter itself never authorizes
sealed execution and never reclassifies previously exposed test data as fresh
sealed evidence.
