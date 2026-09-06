# HAI23 label and summary physical-interval mismatch — V1

## Status

`HAI23_SUMMARY_LABEL_INTERVAL_MISMATCH` is a fail-closed blocker for the
requested exact physical-interval resolution.

The public official-metadata boundary remained active. Only timestamp and
binary attack-label columns were selected from the two official HAI23 label
payloads. No SCADA feature values, method execution, prediction, or metric was
accessed.

## Enumerative evidence

The exact payloads replayed their supplied SHA-256 and byte-size authorities.
The official README, technical manual, summary record listings, and binary
label positive-run census agree on 14 occurrences for the control panel and
38 occurrences for the evaluated panel. The manual blocks are respectively
`A101-A114` and `A201-A238`.

The evaluated summary's scalar declared count remains 40. It conflicts with
the four enumerative census signals, but the task cannot accept the
enumerative structure as an exact physical interval authority because of the
following separate mismatch.

## Physical coordinate mismatch

The control panel's 14 label ranges match its 14 listed summary intervals at
both exact endpoints. For the evaluated panel, all 38 label positive ranges
are represented at a coarser minute-level timestamp coordinate. None of the
38 endpoint pairs equals the corresponding second-level summary endpoint pair.
All 38 pairs align only after flooring the summary endpoints to minutes.

No authority authorizes that conversion, inference of seconds, or selection of
one source as the physical endpoint authority. Therefore no test2
occurrence-to-interval join was accepted.

## Required next authority

An official, version-bound explanation must define the relationship between
the evaluated label-file timestamp coordinate and the summary's second-level
physical timestamps, including any precision restoration or endpoint rule. A
researcher-defined floor/rounding rule is not acceptable.
