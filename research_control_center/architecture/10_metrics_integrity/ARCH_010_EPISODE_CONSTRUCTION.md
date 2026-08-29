# Alarm Episode Construction

The constructor receives integer physical-row alarm indices. It set-deduplicates and sorts them, then merges only exact row adjacency (`current == previous + 1`). The allowed gap is zero rows. Each maximal run becomes a half-open `[start,end)` interval. The canonical validator rejects empty, overlapping, adjacent, or out-of-range output intervals.

Duplicates from multiple D1 rule records at the same decision row collapse before grouping. First and last rows are handled by normal interval opening/closing. The helper uses row positions, not wall-clock timestamps; interpreting adjacency as one second depends on the frozen one-second sampling contract. It does not independently validate missing wall-clock timestamps or carry a file identifier.

The same episode semantics are used across the frozen D0, normalized D1, D2 V1, and D2 V2 metric paths, even though thin method-specific wrappers are separate.
