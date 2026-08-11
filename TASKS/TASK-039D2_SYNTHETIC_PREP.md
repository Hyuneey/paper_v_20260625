# TASK-039D2-PREP: Synthetic-Only One-Way Confirmation Engine Preparation

## Status

`passed_task039d2_synthetic_preparation`

This status means only that the future confirmation implementation exists and
its synthetic semantics pass. It is not a TASK-039D2 scientific result or an
authorization to access real HAI values.

## Frozen base and policy

- Base commit: `360cf4b84ed2c18e026186be00f2312508a8fb85`
- Branch: `task-039d2-synthetic-prep`
- Confirmation policy:
  `83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27`
- D1 audit dependency: none; this preparation remains independent of the D1
  audit outcome and must remain unmerged if that audit fails.

The D0 policy is unchanged: at least five usable responses, unchanged source
direction, selected consistency strictly greater than opposite consistency,
directional consistency at least `0.60`, robust effect ratio at least `1.0`,
and exact reuse of D1 parameters. Every condition is required. Alternative
horizon search, opposite-direction search, and lower-ranked fallback are
prohibited.

## Data and authority boundary

- Real HAI access: `false`.
- Train1, train2, train3, train4, test, labels, and attacks: not opened.
- D1 private ledgers: not opened.
- Synthetic D1 records: clearly marked test-only values.
- `D2_REAL_EXECUTION_AUTHORIZED`: `false`.
- Rule v2 authority: `false`.
- Real-data CLI: absent.

The future real-file entry point validates a self-hashed
`TASK039D2AuthorizationV1` before any path operation. No authorization instance
or real runner exists on this branch. There is no bypass flag.

## Implementation contract

`ConfirmableDirectionalRelationV1` freezes the source, source step direction,
target, target response direction, D1-selected horizon, source numeric-record
references, target scale-record reference, and D1 directional-record hash.

`D1ParameterLedgerBindingsV1` exposes only the source and target private-ledger
hashes. Immutable D1 source and target record wrappers verify exact self-hashes
before their numeric values can be used. This prevents in-place parameter
changes and ensures relation references resolve to the supplied frozen records.

The synthetic engine:

1. requires all twelve frozen source identities;
2. extracts source events once with the unchanged D1R linear helper;
3. applies the unchanged D1R indexed all-source inclusive `+/-2` isolation;
4. filters only the exact D1 source direction;
5. evaluates only the exact D1 horizon with the unchanged optimized response
   helper;
6. scores only the exact D1 target direction;
7. delegates its decision to the D0 confirmation gate; and
8. emits only `calibration_confirmed` or `calibration_conflict`.

Candidate-arm provenance is absent from every confirmation input. META rank or
tier, STAT score or horizon, GDN rank/similarity/frequency, origin arms, and
overlap category cannot be supplied. Method provenance may be joined only
after future D2 outcomes freeze.

## Synthetic verification matrix

The tests cover:

- confirmed and insufficient-support relations;
- the exact five-response boundary;
- consistency exactly `0.60` and just below it;
- robust effect exactly `1.0` and just below it;
- selected consistency greater than, equal to, and below opposite consistency;
- right censoring without imputation;
- step-up and step-down sources;
- increasing and decreasing targets;
- all-twelve-source isolation and the inclusive `+/-2` boundary;
- immutable selected horizon and target direction; and
- parity of the optimized wrappers with the frozen D0/reference helpers.

Anti-retuning tests cover all source and target numeric parameters, both
directions, selected horizon, pre/post/response windows, refractory period,
isolation radius, alternative-horizon search, opposite-direction search, and
lower-ranked fallback.

## Required handoff

This branch may be reviewed as an implementation-preparation artifact. It must
not be merged or used for real D2 execution unless TASK-039D1 passes its
independent audit and a later task supplies explicit D2 authorization.
