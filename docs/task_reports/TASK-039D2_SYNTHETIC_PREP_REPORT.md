# TASK-039D2-PREP Synthetic Preparation Report

## Result

Status: `passed_task039d2_synthetic_preparation`.

The future one-way confirmation engine has an immutable, arm-blind,
synthetic-only implementation path. This is preparation evidence only. No real
TASK-039D2 confirmation was executed, no D2 authority was created, and Rule v2
remains unauthorized.

## Frozen bindings

| Binding | Value |
|---|---|
| Base commit | `360cf4b84ed2c18e026186be00f2312508a8fb85` |
| Branch | `task-039d2-synthetic-prep` |
| Confirmation policy | `83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27` |
| Execution mode | `synthetic_only_preparation` |
| D2 real execution authorized | `false` |
| Rule v2 authorized | `false` |

## Implementation evidence

- `ConfirmableDirectionalRelationV1` freezes the D1 relation identity,
  directions, horizon, parameter references, and directional record hash.
- `D1ParameterLedgerBindingsV1` exposes only source and target ledger hashes.
- Exact D1-shaped source and target records are immutable and self-hash
  checked. The checked-in source includes no production D1 fixture values.
- Linear event extraction, indexed all-source isolation, and optimized target
  response evaluation are reused without changing the D1 optimized module.
- The final decision delegates to the unchanged D0 confirmation gate.
- The engine has no horizon loop, direction loop, fallback, retuning argument,
  provenance input, file reader, CLI, or bypass flag.

## Synthetic and negative tests

Focused unittest discovery executed 19 tests and passed all 19. The named
synthetic matrix contains 19 cases:

1. confirmed relation;
2. insufficient train3 support;
3. exact five-response boundary;
4. consistency exactly `0.60`;
5. consistency just below `0.60`;
6. effect exactly `1.0`;
7. effect just below `1.0`;
8. selected consistency greater than opposite;
9. equality fails;
10. opposite greater fails;
11. right censoring;
12. step-up;
13. step-down;
14. target increase;
15. target decrease;
16. all-twelve-source isolation;
17. inclusive `+/-2` boundary;
18. immutable selected horizon; and
19. immutable target direction.

Fifteen no-retuning checks cover source noise scale, source threshold, source
stability tolerance, target scale, source direction, target direction, selected
horizon, pre-window, post-window, response window, refractory period, isolation
radius, alternative-horizon search, opposite-direction search, and lower-ranked
fallback. Arm-blindness checks reject META, STAT, GDN, origin-arm, and overlap
inputs.

## Access and authority receipt

| Question | Result |
|---|---|
| Real HAI files accessed | `false` |
| D1 private ledgers accessed | `false` |
| D2 authorization present | `false` |
| Real D2 execution possible | `false` |
| Method provenance joined | `false` |
| Rule v2 authorized | `false` |

The future real-file scaffold calls the authorization guard before any path
operation and then stops because this branch intentionally contains no real
runner. A self-hashed `TASK039D2AuthorizationV1` must be supplied by a later,
explicitly authorized task before the guard can pass.

## Claim boundary

The passing status establishes implementation availability and synthetic
semantic parity only. It is not evidence that any real P1 relation confirms on
train3, is valid as a rule, improves a detector, or has causal meaning.
