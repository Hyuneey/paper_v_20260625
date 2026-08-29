# ARCH-007 Prediction Freeze Boundary

Classification: `DURABLE_PREDICTION_FILE_BEFORE_LABEL`.

The D0 execution builds a 54,000-record label-blind `ScientificDetectorPredictionArtifactV1`, atomically writes the public JSON artifact, reads those bytes back, validates schema/record closure/self-hash, and only then transitions to `PREDICTION_FROZEN`. `_load_label_custody_once_v1` calls `require_label_access()` and rejects any earlier label access.

After labels are parsed, metric code reopens the persisted prediction file and requires byte-for-byte equality with the pre-label frozen bytes both before and after metric generation. This creates a durable process/file boundary stronger than the frozen D1 pilot's shallow in-memory object boundary.

The artifact records row index, alarm boolean, decision identity, source/model/threshold/feature hashes, a score-vector content hash, and point-alarm count. Numeric scores and the private threshold are not published.

This proves ordering and custody for the frozen execution. It does not by itself validate detector performance or fresh-machine reproduction.

