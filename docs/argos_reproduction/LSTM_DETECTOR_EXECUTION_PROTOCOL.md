# LSTM Detector Execution Protocol

TASK-037B executes exactly ten frozen KPI series under both official EasyTSAD
LSTMAD variants and seed `20260723`. `LSTMADalpha` and `LSTMADbeta` are
co-primary provenance-sensitivity arms; no metric ranks, removes, or selects a
variant.

Each unit uses the pinned TASK-037A rootless Podman image with no network,
non-root UID, read-only root, dropped capabilities, no new privileges, one CPU,
1 GB memory, 64 PIDs, and a 300-second bounded container timeout. The container
receives one split's values, the frozen config, and checkpoint/normalization
files when scoring. Labels, another KPI, rules, provider credentials, the
repository root, and sealed-test artifacts are never mounted.

Generation is divided chronologically inside the official `naive` fit into 80%
model training and 20% early-stopping validation. Both remain within the frozen
generation split. The train subpartition fits min-max normalization. The
`contaminated_training` policy retains all generation values and does not mount
or use generation labels during fitting.

Generation and inner scores are replayed twice before inner labels are loaded.
Checkpoints, normalization, score hashes, inner thresholds, predictions and
generation error-segment hashes are frozen before outer access. Outer inference
is then replayed twice from the frozen checkpoint without labels; metrics are
computed only after all outer score and prediction hashes are frozen.

The run does not execute rules, providers, agents, detector fusion, or the
sealed test.
