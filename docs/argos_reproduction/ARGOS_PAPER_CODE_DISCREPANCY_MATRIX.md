# ARGOS Paper-Code Discrepancy Matrix

## Scope

- Paper: `https://arxiv.org/abs/2501.14170`
- Pinned implementation: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Historical Aggregator candidate: `c03427f2ab16e377946d4c1176585156ddae7254`
- Method: source and paper inspection only

| Topic | Paper description | Pinned implementation | Historical implementation | Consequence |
|---|---|---|---|---|
| Rule-only mode | Detection, Repair, and Review agents iteratively construct rules. | `train-LLM-only` remains documented and implemented. | Rule-only mode is also present. | The pinned commit is the frozen first reproduction target. |
| Aggregator or combined mode | FP and FN rules correct corresponding base-detector error subsets. | Combined modes remain in code but are absent from the current README. | `c03427f` README documents `train-combined-fn`, `train-combined-fp`, and Aggregator usage. | Historical documentation is needed, and a complete run still needs detector artifacts and likely an adapter. |
| Chunk sampling | Multiple chunks are supplied to candidate generation; dataset-specific chunk sizes are reported. | Train chunks are sampled with `np.random.randint(0,1000)` and modulo chunk count. | Similar iterative sampling exists. | Sampling can repeat chunks and is sensitive to NumPy call order. |
| Random seed | Results are reported across repeated trials. | NumPy is seeded to `8`; provider generation has no seed; retry jitter uses unseeded Python randomness. | No complete end-to-end seed contract is evident. | Exact provider-level reproduction is not guaranteed by the code seed. |
| RepairAgent | Repairs rules that cannot execute correctly. | Executes generated Python with `exec`; the timeout wrapper currently calls directly. | Also executes generated Python. | Repair behavior is not reproduced because generated-code execution is prohibited. |
| ReviewAgent | Uses validation feedback to prevent degradation and refine rules. | Rule-only review compares current and previous performance on the full train frame, then returns a test evaluation. | Uses generated-code execution and performance feedback. | The paper's validation wording does not match the pinned review feedback split. |
| Validation selection | Top candidates are retained using validation accuracy. | `TrainPerfSelector` ranks by validation Event-F1-PA F1. | `c03427f` selector ranks by train point F1. | Pinned and historical selection semantics must not be conflated. |
| Threshold handling | Rule predicates and evaluation thresholds contribute to reported results. | LLM writes internal Python thresholds; evaluation utilities separately search label-aware score thresholds. | Point-F1 threshold search is prominent. | Rule thresholds are not calibrated by an ARGOS optimizer; evaluation thresholds are a distinct mechanism. |
| Point-F1 | Reported as one evaluation view. | Computed from rule scores with precision-recall optimization. | Used for historical candidate selection. | Point-F1 behavior differs from pinned Event-PA selection. |
| Point-adjusted metrics | Included in the experimental metric set. | Point-F1-PA is computed using labels from the evaluated split. | Available through evaluation utilities. | It is paper-faithful diagnostic behavior, not the proposed method's primary policy. |
| Event-PA | Primary paper metric for anomaly events. | Event-F1-PA is computed and used by the pinned validation selector. | Historical selector predates this pinned validation path. | Pinned candidate ranking is label-aware Event-PA on validation. |
| Final rule selection | Top validation candidates support the reported model. | Selected rules are propagated across iterations, but ReviewAgent evaluates test every iteration and finalization has no single sealed-test gate. | Selected rules are explicitly tested during iterations. | The source does not satisfy a sealed final-test protocol. |
| Generated Python execution | Rules are executable Python functions. | Detection extracts a fence; Repair and Review execute it through `exec`. | Same unrestricted execution model. | Runtime and performance reproduction remain gated on a verified container boundary. |
| Dataset preprocessing | Paper describes dataset conversion and dataset-specific settings. | `ArgosDataset` expects `value,label,index`; README-referenced preprocessing utility is missing from the pinned tree. | Historical audit did not find a compatible complete preprocessing utility. | TASK-024 uses a separately documented minimal adapter; it is a deviation, not copied upstream behavior. |
| Combined validation | Aggregator rules are selected using validation behavior. | Combined `eval_val()` calls combined train evaluation. | Historical selection uses train F1. | The documented paper path is not directly runnable with paper-faithful validation semantics. |
| Final combined evaluation | Both FP and FN corrective rules are applied around a detector. | `eval-combined` constructs FN mode and accepts one rule; dual-path helper is not fully wired. | README describes the broader Aggregator workflow. | A minimal adapter is required for a frozen detector-only versus rule-only versus combined comparison. |

## Claim boundary

The audit establishes source behavior and discrepancies. It does not reproduce
rule execution, agent effects, detector predictions, KPI metrics, or paper
performance.
