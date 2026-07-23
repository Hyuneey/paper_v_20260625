# Detector Error Segment Protocol

After generation predictions are frozen, trusted host code compares them with
generation labels and constructs maximal contiguous TP, FN, FP and TN runs.
Internal and ARGOS compatibility intervals are half-open `[start, end)`, which
matches the pinned ARGOS `iloc[start:end]` consumer.

Segments are sorted and non-overlapping within category. Private manifests bind
the variant, KPI, threshold record and prediction hash. Tracked reports contain
only segment counts, point counts and manifest hashes. Raw positions remain
ignored.

`TrainLabels/<KPI ID>.npy` and `IncorrectIndices/train.json` are kept in
separate alpha and beta roots. `TestLabels` creation is prohibited. TASK-037B
does not use the segments for rule generation.
