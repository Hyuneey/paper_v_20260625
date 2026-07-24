# Branch Candidate Lineage

Each tracked candidate retains its branch, original slot, detector variant,
KPI, direction, initial rule hash, parent rule hash, output rule hash, repair
reuse key, Review call identity, terminal state, and output origin.

Prediction references are reused as follows:

- A0 and A1 initial identities: TASK-037E frozen inner predictions.
- A1 repaired outputs: TASK-038C repaired-parent inner predictions.
- A2/A3 no-review identities: TASK-038C parent predictions.
- A2/A3 reviewed outputs: TASK-038C reviewed predictions.

Every reference must match its committed expected hash. Missing artifacts may
only be recovered by exact two-run replay with the frozen runtime and values.
A changed hash is rejected. Tracked manifests contain hashes and counts, not
source, arrays, labels, or local paths.
