# TASK-037A Report

Final status: `unresolved_variant_ambiguity_with_dual_arm_freeze`.

The ARGOS paper and repository recover the KPI detector family as LSTMAD but do
not disambiguate EasyTSAD's seq2seq `LSTMADalpha` and multi-step
`LSTMADbeta`, nor publish the winning detector configuration. Both variants are
therefore frozen as co-primary provenance-sensitivity arms; performance-based
selection between them is prohibited.

Official EasyTSAD `0.2.0.2` commit `55eff2c...` is pinned as the time-bounded
pre-paper source. Required source/config files were hash-verified. The isolated
WSL-native rootless Podman image passed network-none, non-root, read-only-root,
CPU, memory and PID controls.

Both variants completed two deterministic synthetic fits, created checkpoints,
returned finite aligned scores and binary predictions on six synthetic cases,
and reproduced model-state and score/prediction hashes. This proves only
environment and execution plumbing. No real KPI value or label was parsed, no
performance metric or fusion was computed, and the sealed test remains
unaccessed.

E4/E5/E6 are protocol-frozen but not authorized. TASK-037B requires a separate
approval.

## Verification

- TASK-037A targeted tests: 15 passed.
- Host regression suite outside the existing optional PyTorch boundary: 371
  passed.
- Broad host discovery retains eight known collection errors because PyTorch is
  not installed in the host environment. TASK-037A did not install or alter
  host PyTorch; detector validation used the pinned isolated container.
- Python compilation, JSON parsing, `pip check`, report self-hash checks and
  `git diff --check` passed.
