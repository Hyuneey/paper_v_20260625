# Normal False Episode Definition

A normal false episode is a complete alarm episode that overlaps **no** attack-event unit.

- An episode wholly in normal rows counts once.
- An episode with any attack overlap is excluded from the normal-FP numerator.
- A mixed normal/attack episode is not split at the boundary.
- Merely touching a half-open attack boundary is not overlap.

The FAR numerator therefore counts episodes, not normal alarm points and not point-level false positives. The denominator is independent: all strict label-`0` rows contribute to normal exposure, including normal rows adjacent to or within the normal portion of a mixed episode.
