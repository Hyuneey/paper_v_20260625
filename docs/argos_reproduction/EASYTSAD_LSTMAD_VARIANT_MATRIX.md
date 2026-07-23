# EasyTSAD LSTMAD Variant Matrix

Frozen source: EasyTSAD `0.2.0.2`, commit `55eff2c6d62f9c792bf6253c046dcc04636efe5a`.
Exact file hashes are recorded in
`TASK-037A_SOURCE_ALIGNMENT_REPORT.json`.

| Field | LSTMADalpha | LSTMADbeta | Provenance |
|---|---|---|---|
| Architecture | LSTM encoder plus autoregressive LSTM decoder | LSTM encoder plus linear multi-step head | Exact source |
| Window | 100 | 100 | Official default |
| Horizon | 3 | 3 | Official default |
| Hidden size | 20 | 20 | Official default |
| Layers | 2 | 2 | Official default |
| Dropout | Not configured | Not configured | Exact source |
| Batch size | 128 | 128 | Official default |
| Epochs | 100 | 100 | Official default |
| Optimizer | Adam | Adam | Exact source |
| Learning rate | 0.0008 | 0.0005 | Official default |
| Loss | MSE | MSE | Exact source |
| Scheduler | StepLR, step 5, gamma 0.75 | Same | Exact source |
| Early stopping | Validation loss, patience 3 | Same | Exact source |
| Preprocess | Train-fitted min-max | Same | Official default |
| Training labels | Loaded but not used by model training | Same | Exact source |
| Score | Overlapping horizon squared errors, averaged | Same | Exact source |
| Random seed | Not set in class | Not set in class | Exact source |

EasyTSAD supports naive, all-in-one, and zero-shot schemas. ARGOS does not
identify which was used. The future KPI detector contract freezes `naive`
because the paper describes per-metric KPI operation, but labels this as a
project-owned closest-reproducible choice rather than an ARGOS-specific fact.

The official score is shorter than the source series. EasyTSAD evaluation
right-aligns it by trimming the label prefix. The synthetic compatibility
wrapper preserves right alignment by explicit zero left-padding; that adapter
choice must remain separately versioned in a real run.
