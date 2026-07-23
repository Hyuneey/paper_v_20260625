# Detector Artifact Contract

Future detector artifacts remain ignored and private. Each KPI and variant has
checkpoint, normalization, generation/inner/outer scores, corresponding binary
predictions, generation error segments, and one inner threshold record. No test
artifact is permitted before joint sealed-test approval.

Tracked manifests contain detector identity/role, EasyTSAD commit and source
hashes, config/environment/seed, KPI ID and split-manifest hash, every private
artifact hash, the threshold and protocol hash, generation incorrect-index
hash, and terminal artifact status.

Hashes establish integrity, not detector quality. Raw scores, predictions,
labels, checkpoints, and paths are not tracked.

The future ARGOS adapter may materialize:

- `TrainLabels/<KPI ID>.npy`
- `IncorrectIndices/train.json`

It must not create `TestLabels` until a separately approved joint sealed-test
run.
