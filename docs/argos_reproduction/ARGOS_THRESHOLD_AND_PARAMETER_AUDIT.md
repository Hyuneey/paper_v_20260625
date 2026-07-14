# ARGOS Threshold and Parameter Audit

## Threshold taxonomy

| Threshold or parameter | Created by | Data split used | Optimization method | Claim status |
|---|---|---|---|---|
| Numeric conditions inside generated Python | LLM in Detection, Repair, or Review output | Labeled prompt chunks and prior rule/feedback | No explicit ARGOS-side search over rule constants; provider writes or revises code | Confirmed source behavior; values are provider-dependent, not calibrated artifacts. |
| Rule-score Event-F1-PA threshold | `EventF1PA.calc()` | Whichever frame is passed to `ReviewAgent.eval`: train, validation, or test | Sort smoothed rule scores and select the threshold with maximum Event-F1-PA F1 using labels from that same split | Confirmed. This is evaluation-label optimization, not an LLM rule constant. |
| Rule-score Point-F1-PA threshold | `PointF1PA.calc()` | Same evaluation split | Search score ordering for maximum point-adjusted F1 | Confirmed diagnostic; not used by pinned `eval()` to create final rule labels. |
| Point-F1 operating point | `PointF1.calc()` | Same evaluation split | `precision_recall_curve` and maximum F1 | Confirmed metric optimization; pinned implementation does not retain its threshold. |
| Historical `c03427f` rule threshold | `calculate_point_f1()` | Train for candidate selection; test during per-iteration evaluation | Precision-recall threshold maximizing point F1 | Confirmed historical behavior; different from pinned Event-F1-PA selection. |
| Base-detector threshold | External detector/EasyTSAD artifact | External pipeline, not established by ARGOS loader | `get_model_labels()` can read an Event-F1-PA threshold from an external evaluation JSON | Utility confirmed, but pinned combined evaluation normally loads ready-made `TrainLabels`/`TestLabels`; threshold provenance is external. |
| `threshold_fn` / `threshold_fp` arguments | Caller defaults to 0.0 | None | No optimization | Present but unused in `combined_inference*`; commented result fields show they are stale interface parameters. |
| Validation selection threshold | Evaluation utility | Validation in pinned rule-only mode | Per-candidate Event-F1-PA threshold search, followed by selector ranking on validation Event-F1-PA F1 | Confirmed for pinned rule-only only. Combined `eval_val()` uses train instead. |
| Chunk size | User/config; paper describes calibration | Paper says training set; pinned CLI accepts an integer | Paper: select size with highest training F1 using DetectionAgent-only runs. Pinned audited path has no calibration routine. | Paper-supported, not reproduced by pinned training path. |
| `top_k` | User CLI | Validation performance determines survivors | Generate `top_k` candidates; keep `rule_per_group` by selector | Not an anomaly threshold. |
| Iteration/time thresholds | Config and CLI | Not data-dependent | `max_iter`, elapsed-time limits, and review timeout constants | Control-flow limits only. |

## Important distinctions

The generated rule's internal comparisons and the evaluator's score threshold
are separate. The rule returns raw binary labels, `smooth_labels(window_size=3)`
turns them into continuous scores, and `EventF1PA` searches a score cutoff using
the labels of the current evaluation split. A report field named `threshold`
therefore does not prove that ARGOS calibrated the Python rule's internal
constants.

The threshold search is repeated independently on train, validation, and test
whenever `eval()` is called on those splits. Consequently, test metrics in the
pinned training loop use a test-label-optimized score cutoff. That behavior is
paper-faithful audit evidence only and is prohibited for the `paperworks`
proposed method.

## Parameter control

- `chunk_size`, `train_test_split`, `top_k`, `rule_per_group`, model name,
  timeout, sample count, and max iterations are explicit CLI/config values.
- NumPy chunk sampling uses seed 8.
- LLM temperature is fixed to 0.75 in Detection, Repair, and Review agents.
- No provider seed is passed.
- Python `random.uniform()` retry jitter is not seeded.
