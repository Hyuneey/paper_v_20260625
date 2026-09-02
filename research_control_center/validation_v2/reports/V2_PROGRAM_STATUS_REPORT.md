# VALIDATION V2 Program Status

## Verdict

`NORMAL_ONLY_TRACKS_COMPLETE_EXP04_NEXT`

The shared V2 foundation, official normal-only custody, EXP-01, the separate
EXP-01B GDN-XAI experiment, EXP-02 numeric selection, and the Formal V4 V2A
portfolio are complete. The exact next scientific work is EXP-04 label-blind
prediction followed by durable freeze. test1 labels remain unopened.

The historical `BLOCKED_NORMAL_DATA_NOT_FOUND` record is preserved. Its root
cause remains `HAI_CODE_MATERIALIZATION_POLICY_NOT_PROPAGATED_TO_V2_RECOVERY_LOGIC`;
it is not the current program state.

## Formal V4 authority

- `DEC-020 = APPROVED_FORMAL_V4`
- `DG-01 = RESOLVED_BY_USER`
- Formal V4 controls validity, numeric binding, replay, portfolio freeze,
  runtime authorization, and custody
- canonical `RuleV1` / `VerifierV1` remain adjacent components rather than the
  direct VALIDATION V2 runtime authority
- canonical-to-V4 bridge: `NOT_SELECTED`

## Completed normal-only work

| Track | Status | Frozen outcome |
|---|---|---|
| EXP-01 | `COMPLETE_QA_PASS` | GDN demoted; `META_PLUS_STAT` selected |
| EXP-01B | `COMPLETE_NORMAL_ONLY` | nine CUDA runs; `GDN_ABLATION_ONLY` |
| EXP-02 | `COMPLETE_QA_PASS` | 37 policies; `RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05` |
| V2A portfolio | `FROZEN_RUNTIME_AUTHORIZED` | 39 Formal V4 directional rules |
| Stronger detector | `READY` | fixed normal-only Isolation Forest |
| EXP-04 | `READY_WITH_CONDITIONS` | all predictions must freeze before test1 labels |
| EXP-05 | `BLOCKED_BY_RUNTIME_TRACE` | waits for actual V2 runtime traces |

EXP-01B observed a small combined-view equal-budget gain, but failed the
preregistered split non-degradation, positive functional effect, and unique
executable-rule conditions. The old EXP-01 negative result remains visible and
unchanged. No V2B primary GDN portfolio was created.

## Reproducibility and optimization

The fresh-machine synthetic rehearsal remains PASS. The EXP-01B public-lineage
replay was optimized without changing checkpoints, data, seeds, models,
hyperparameters, or selection rules: scalar CUDA-to-host synchronization was
replaced by equivalent vector aggregation and private atomic per-checkpoint
caches. Independent replay found zero result mismatch and preserved the frozen
`GDN_ABLATION_ONLY` disposition.

## Safety accounting

- normal-only scientific executions: 3
- test1 accesses: 0
- label accesses: 0
- test2 accesses: 0
- held-out accesses: 0
- provider/LLM calls: 0
- result-driven redesigns: 0
- private exposures in public outputs: 0
- PILOT V1 modifications: 0

## Exact next

Run `V2-SCI-EXP04-001`: generate D0, fixed Isolation Forest, V2A Rule-only,
and preregistered fusion predictions label-blind; atomically persist and replay
all predictions; only then authorize DEVELOPMENT_ONLY test1 labels. DG-05
remains mandatory before any held-out or test2 access.
