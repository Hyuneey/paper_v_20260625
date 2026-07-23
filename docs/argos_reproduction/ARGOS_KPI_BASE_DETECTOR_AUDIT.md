# ARGOS KPI Base-Detector Audit

## Decision

DEC-061 status is `detector_family_recovered_variant_ambiguous`.

The ARGOS paper identifies the KPI base-detector family as **LSTMAD**, but it
does not name `LSTMADalpha` or `LSTMADbeta`, give an EasyTSAD commit, publish a
detector configuration, or identify the training schema. The pinned and
historical ARGOS repositories likewise contain no detector trainer or variant
name. They consume externally produced detector artifacts.

Accordingly, TASK-037A does not claim exact detector reproduction. DEC-062
retains both official EasyTSAD variants as co-primary provenance-sensitivity
arms. Selecting between them by inner or outer performance is prohibited.

## Primary-source evidence

- The [ARGOS paper](https://arxiv.org/abs/2501.14170) lists
  AnomalyTransformer, AutoRegression, FCVAE, LSTMAD, and TFAD; reports LSTMAD
  as the highest-F1 KPI baseline; selects the highest training-set-F1 baseline
  per dataset; and trains KPI FN rules from LSTMAD training false negatives.
- The paper says deep-learning configurations were grid-searched per dataset,
  but does not publish the winning LSTMAD variant or grid result.
- Pinned [microsoft/ARGOS](https://github.com/microsoft/ARGOS) commit
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` accepts `model_res_path` and reads
  `IncorrectIndices/train.json`, `TrainLabels/<curve>.npy`, and
  `TestLabels/<curve>.npy`; it does not fit LSTMAD.
- Official [EasyTSAD](https://github.com/dawnvince/EasyTSAD) distinguishes
  `LSTMADalpha` (seq2seq) from `LSTMADbeta` (multi-step prediction). Its
  [PyPI metadata](https://pypi.org/project/EasyTSAD/) confirms both class names
  and package releases.

## Recovered and unresolved fields

| Question | Finding |
|---|---|
| Detector family | LSTMAD, source-supported |
| Exact EasyTSAD class | Unresolved |
| ARGOS detector config | Unresolved |
| ARGOS EasyTSAD revision | Unresolved |
| ARGOS training schema | Unresolved |
| Baseline selection scope | Per dataset, from paper wording |
| Hyperparameter selection | Highest training-set F1 after per-dataset grid search |
| Score/threshold provenance | External to pinned ARGOS |

The project freezes EasyTSAD `0.2.0.2` commit
`55eff2c6d62f9c792bf6253c046dcc04636efe5a`, the last official repository
revision before the January 2025 ARGOS paper release. This is a time-bounded
reproducibility choice, not evidence that ARGOS used that exact commit.

The local audit inspected `driver.py`, `datasets/dataset.py`, and
`common/common.py` in ARGOS, and both `Methods/LSTMAD*` directories,
`TrainingSchema/Naive.py`, `DataFactory/TSData.py`, and the Point/Event F1-PA
protocols in EasyTSAD. Their hashes are recorded in the source-alignment
report.

## Repository fusion boundary

Pinned `combine_labels` uses elementwise maximum for FN compensation and
elementwise minimum for FP correction. The pinned `eval-combined` driver does
not expose the paper's complete two-family Aggregator. Detector artifacts are
produced outside that driver.
