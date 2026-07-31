# TASK-039P1D GDN Optional Import and Fidelity Freeze

## Status

`passed_gdn_optional_import_and_fidelity_freeze`

## Implemented

- Torch and Torch Geometric are an explicit `gdn` optional dependency group.
- Lightweight `paperworks`, `paperworks.gdn`, `paperworks.candidates`, and
  `paperworks.e2e` imports do not load Torch or PyG.
- Historical Torch-specific package exports resolve lazily and fail through
  `GDN_OPTIONAL_DEPENDENCY_UNAVAILABLE` when unavailable.
- The pinned upstream GDN commit and seven required files are frozen by Git
  blob SHA and SHA-256.
- Three deterministic fidelity records freeze the current trainers as smoke
  only and the masked extractor as a project-owned component.
- The existing Torch backend model and training-function AST is unchanged.

## Boundary

Only a future `upstream_aligned_validated` backend may be identified as GDN in
RQ1. The production graph-ranking backend remains pending until TASK-039A/B.

TASK-039P1A, P1B, P1C, and P1D are complete. Parent TASK-039P1 is complete;
the next task is TASK-039A.

No data, model training, provider, Agent, detector, rule runtime, outer, or
sealed execution occurred.
