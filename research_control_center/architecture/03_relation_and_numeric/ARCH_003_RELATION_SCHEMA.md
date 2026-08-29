# ARCH-003 Relation Schema

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Identity

A frozen relation is not pair-only. Its identity contains:

- `source`
- `source_step_direction` (`step_up` or `step_down`)
- `target`
- `target_response_direction` (`increase` or `decrease`)
- `selected_delay_horizon_seconds`
- hashes of the fit record, train3 confirmation record, and relation family

Therefore one source-target pair can yield zero, one, or two relations because the two source-step directions are evaluated independently. Only one target-response direction and one horizon survive for each source direction. Multiple horizons do not survive.

## Lifecycle terms

| Term | Exact meaning |
|---|---|
| Candidate pair | One source-target identity proposed by META, STAT, or GDN; it has no confirmed sign or horizon. |
| Fit-supported relation candidate | A source-sign/target-sign/horizon record selected on normal train1/train2 and passing all fit gates. |
| Calibration-confirmed relation | The same frozen identity passes the one-way normal train3 gate without retuning or alternate search. |
| Executable numeric authority | A separately governed, hash-bound set of normal-only numeric references accepted for construction or runtime. |

“Directed” means that source, source-step sign, target, expected target-response sign, and delay horizon are ordered. It does not mean causal direction.

## Sanitized example

`SOURCE_A | step_up -> TARGET_B | increase | 5-second selected horizon`

This says that repeated isolated `step_up` events in the normal fit data were followed consistently enough by an above-noise increase at the selected horizon and then passed train3 confirmation. It does not prove physical causation, global lag optimality, or held-out generalization.

