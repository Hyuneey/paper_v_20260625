# Attack-event Unit Construction

## Authority

The frozen INNER label authority is the pinned HAI 23.05 `label-test1.csv` contract: exact columns `timestamp,label`, 54,000 ordered rows, exact timestamp alignment to test1 features, and strict string labels `0` or `1`. This audit used only existing sanitized manifests and result-integrity records; it did not open the private label payload.

## Algorithm

`MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL` scans the ordered binary label vector. A `0→1` transition opens an event and the next `1→0` transition closes it. A terminal sentinel closes a run at end-of-file. Units are half-open intervals `[start,end)` and adjacent positive rows remain in the same unit. A zero row separates units.

The frozen test1 authority is one file and produces exactly **14 contiguous attack-event units**. The generic interval helper carries integer positions rather than file IDs, so file-locality is supplied by the caller contract; generic multi-file flattening is not independently prevented by the helper.

## Independence

The grouping policy establishes operational units, not statistical independence. No frozen independence analysis exists. Therefore the correct current wording is **14 contiguous attack-event units; statistical independence not established**.

## Evidence

- `src/paperworks/v6/task039e3_r2r_utility_evaluator_metrics_v1.py`: strict-label validation, event construction, overlap and Recall.
- Frozen D0/D1/D2 metric artifacts under `docs/task_reports/`: event count and policy identity.
