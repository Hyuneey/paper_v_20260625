# HAI 23.05 Label Custody

Labels and attack summaries are accessed only to verify integrity, binary
domain, test timestamp alignment, and aggregate event counts. Event-level
content is written to a private custody artifact outside this repository.

Public records may expose only hashes, sizes, header hashes, row counts,
alignment status, label-domain validity, aggregate event counts, custody
status, and the private artifact SHA-256. Attack times, targets, descriptions,
ordering, and positive-point counts are prohibited.

Label content cannot inform process selection, preprocessing, candidate
construction, calibration, rule work, detector work, or utility selection.

The LFS acquisition gate failed before label content access. No private
custody artifact was created and no label or attack-summary content was read.
