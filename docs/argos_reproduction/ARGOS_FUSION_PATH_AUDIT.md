# ARGOS Fusion Path Audit

## Source alignment

| Role | Commit | Status |
|---|---|---|
| Rule-only audit target | `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` | Pinned checkout and current upstream HEAD at review time |
| Historical Aggregator documentation candidate | `c03427f2ab16e377946d4c1176585156ddae7254` | Best pre-removal README alignment; not the pinned source |

Historical README documentation describes `Argos w/ Aggregator` but leaves the
base-detector incorrect-example preparation step as `TODO`. The pinned README
removes this workflow while much of the combined code remains.

## Exact fusion semantics

`common/common.py::combine_labels` implements:

```text
FN compensation: combined = max(detector_label, rule_label)
FP correction:   combined = min(detector_label, rule_label)
```

The paper's full Aggregator applies FP correction and FN compensation to a copy
of the base labels. For binary labels this matches the min/max interpretation:

1. an FN rule can turn detector `0` into `1` but cannot clear detector `1`;
2. an FP rule can turn detector `1` into `0` but cannot set detector `0` to `1`.

## Artifact contract

The combined dataset loader expects a `model_res_path` with:

- `IncorrectIndices/train.json` containing `FN` and `FP` mappings from curve ID
  to `[start,end]` segments;
- `TrainLabels/<curve>.npy` containing precomputed detector train labels;
- `TestLabels/<curve>.npy` containing precomputed detector test labels.

ARGOS does not derive these detector artifacts in the audited driver. Their
creation, detector checkpoint, detector threshold, alignment, and hashes must be
provided by an external EasyTSAD-style pipeline.

## Training examples

| Mode | Target chunks | Additional contrast chunks | Prompt goal |
|---|---|---|---|
| `train-combined-fn` | Chunks intersecting detector FN segments and containing anomalies | Normal chunks; one-for-all chooses closest mean/std | Detect missed anomalies without affecting normal data. |
| `train-combined-fp` | Chunks intersecting detector FP segments and containing no anomaly | Abnormal chunks; one-for-all chooses closest mean/std | Return normal for detector false positives without clearing real anomalies. |

The paper says one-for-one contrast examples are random. The pinned code samples
the target train chunk with seeded NumPy randomness but retrieves one-for-one
contrast chunks by iteration index; this is a paper/code discrepancy.

## Evaluation and executability

- `combined_eval(...,"train")` uses precomputed detector train labels and
  `whole_train_df`, then evaluates rule scores and applies min/max fusion.
- `combined_eval(...,"test")` uses precomputed detector test labels and the test
  frame.
- Pinned `eval_val()` routes combined modes to `combined_eval(...,"train")`, so
  it does not perform the validation-set fusion described by the paper.
- Historical `c03427f` selects candidates using train F1 and explicitly
  evaluates the selected rule on test every iteration.
- Pinned rule-only selection was changed to validation Event-F1-PA, but
  `ReviewAgent.run()` still returns a test evaluation every iteration.
- `driver.py --mode=eval-combined` constructs the engine as
  `train-combined-fn` and accepts one rule path. It does not expose both FP and
  FN rule paths required by the paper's complete Aggregator.
- `combined_inference()` can accept both rule paths, but its `threshold_fn` and
  `threshold_fp` arguments are unused and the driver does not wire this method.

Therefore the historical combined path is behaviorally identifiable but not
currently reproducible as a complete documented paper workflow without explicit
base-detector artifacts and a small paper-faithful adapter.

## Why fusion is used

### Code-supported conclusion

The implementation trains rules on detector error subsets and combines binary
outputs with max for FN compensation and min for FP correction.

### Paper-supported interpretation

The paper states that rules can regress relative to mature detectors, so the
Aggregator constrains each rule family to correct one detector error direction.
It presents rules as corrective signals around an established detector rather
than a universal replacement.

### Experimental question still open

Whether fusion is actually better for the selected KPI series requires frozen
detector-only, rule-only, FN-only, FP-only, and full combined predictions. No
such experiment is run in TASK-029, so no superiority claim is made.
