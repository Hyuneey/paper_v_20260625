# HAI23 resolution-aware official scenario authority — V1

## Resolution

The HAI23 ground-truth sources have distinct, version-bound roles. The manual
defines scenario identity; enumerated summary records define exact physical
interval endpoints; the binary label file independently corroborates event
existence and chronology at its native minute resolution; and the README
corroborates the panel census.

No minute-to-second conversion was recovered or used. The canonical endpoints
are the explicit seconds in the enumerated official summary records.

## Cross-source result

The test1 control remains exact across all four authorities. For test2, all
four enumerative census sources are 38, the native-resolution label comparison
is 38/38 unique, and manual-to-summary matching is 38/38 unique by independent
manual start-minute and duration evidence.

The summary scalar value 40 remains preserved as an internally inconsistent,
non-enumerative metadata field with unknown cause. It has no associated manual
identity, enumerated interval, or label occurrence and creates no scenario.

## Custody and privacy

Exact interval and direct-target records are held only in the private canonical
authority. This public receipt contains hashes, roles, and aggregate counts;
it contains no raw feature rows, prediction, score, or metric data.
