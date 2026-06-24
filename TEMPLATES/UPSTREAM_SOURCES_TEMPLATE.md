# UPSTREAM_SOURCES.md

Record exact revisions before implementation.

## microsoft/ARGOS

- Repository: https://github.com/microsoft/ARGOS
- Reviewed snapshot: 6b24161ff08de069840a1fb4fbaecf7bf8e393f1
- Pinned commit used by this project: `<fill>`
- License: MIT
- Intended use:
  - agent-loop architecture,
  - rule planning/repair/review concepts.
- Code copied or adapted: `<none or list>`
- Explicitly not reused:
  - univariate dataset contract,
  - test evaluation in the training loop,
  - arbitrary Python `exec` rule runtime.

## d-ailin/GDN

- Repository: https://github.com/d-ailin/GDN
- Reviewed snapshot: 9853899da860682669a134e4af315d036aab4eca
- Pinned commit used by this project: `<fill>`
- License: MIT
- Intended use:
  - model architecture reference,
  - sensor embedding and Top-K relation-learning concept.
- Adaptations:
  - modern PyTorch/PyG port,
  - `C_i` candidate mask before Top-K,
  - candidate self-edge exclusion,
  - split-before-windowing,
  - upstream test-tuned scoring not reused.
- Code copied or adapted: `<none or list>`

## SWaT

- Preferred source: official iTrust distribution
- Optional local mirror: researcher-provided Kaggle URL
- Local-only: yes
- Dataset edition: `<fill or unverified>`
- Normal-data version: `<fill or unverified>`
- Terms-of-use reviewed: `<yes/no/date>`
- Raw data committed: no
