# TASK-039D2 Recovered Result Report

Scientific status: `passed_task039d2_one_way_train3_confirmation`

Recovery status: `passed_task039d2r_result_contract_recovery`

TASK-039D2R repaired only the frozen receipt schema's one-key/four-key mismatch.
The four scientific Commit-A files remain byte-identical in Git. No HAI file
was opened and train3 was not reread. Public outcomes were reconstructed from
the original self-hashed 45-record private confirmation ledger.

## Calibration-confirmed candidates

- Directional confirmed/conflict: `42` / `3`.
- Confirmed pairs / D1-supported pairs without confirmation: `23` / `2`.
- META: `15/20` pairs, `28` directions.
- STAT: `17/20` pairs, `32` directions.
- GDN: `3/20` pairs, `5` directions.
- Confirmed union: `23`; shared by exactly two arms: `12`; all three: `0`.

These are calibration-confirmed normal delayed-response relation candidates,
not causal truth, ground truth, verified rules, root causes, or anomaly
performance. No candidate-method winner was selected.

## Recovery boundary

- Original scientific Commit A: `5524262d8a666093f948f7f01491b4a0b03e568e`.
- Result-contract Recovery Commit R: `0b2cdedafa98d99d554812a1a6f421bc482794a9`.
- Original failed status: `failed_task039d2_result_contract`.
- Frozen private ledger: `d349421ae9a866b924c329dcb2546088466866e09f45851ec5d18090509dc062`.
- Train3 reread / HAI values accessed during recovery: `false` / `false`.
- Scientific outcomes recomputed from HAI: `false`.
- Scientific code changed: `false`.
- Rule v2, Agent, detector/runtime authority: `false`.
- Required next task: `TASK-039D2-AUDIT`.
