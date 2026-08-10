# TASK-039C-GDNR Exact Environment Remediation and GDN Execution

Status: `failed_gdn_training`

The only authorized dependency-remediation attempt used CPython 3.12.13 on Windows AMD64 with exact `torch==2.12.1`, `torch-geometric==2.8.0`, and `jsonschema[format-nongpl]==4.26.0`. Wheels were acquired as binaries, rehashed, and installed offline into an external environment.

The run failed closed: seed 11 failed at the frozen PyG 2.8.0 message-passing softmax compatibility boundary. No ranking or top-K result was produced.

The frozen backend passed the process-size integer as the third positional
argument to `torch_geometric.utils.softmax`. Under the exact PyG 2.8.0 API,
that position is the optional pointer argument, so seed 11 terminated with an
`AttributeError` before a seed record could complete. Correcting that call
would require changing the frozen scientific implementation. This remediation
task did not make that change, retry the seed, or use a fallback backend.

Only train1 and train2 in the frozen P1 candidate-learning view were authorized. Train3, train4, test, labels, attacks, BR2 pair supervision, META output, and STAT output were not used. No checkpoint, raw row, raw window, or node embedding was persisted publicly or privately.

Environment receipt hash: `d0602e4f591073d58881aa1f918b788176ed888d5265f5e253fd272e060109c6`.
Wheelhouse receipt hash: `b8e3d5fc7b66e61282d48a6a9aa28872e387534e40ead4cda691433a3bdd8cea`.
Fidelity receipt hash: `93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4`.
Data-access audit hash: `6c1de4784e7cfc3d8f9daf30a7542326aad5030c2dfed9daa1c74630b01cf2dc`.
Execution receipt hash: `f46eb437aa307be41cad593fca8384d226c632738c1336a62c57554e42cf3a80`.

## Verification

- GDNR targeted tests: 23 passed.
- Existing GDN tests: 19 passed.
- TASK-039C0 tests: 38 passed.
- TASK-039P1D fidelity and boundary tests: 18 passed across the exact and
  Torch-free environments required by their respective contracts.
- TASK-039BR0, TASK-039BR1, and TASK-039BR2 regressions: 24, 34, and 43
  passed, respectively.
- TASK-032 frozen regressions: 106 passed.
- Guarded public discovery: 593 runnable tests passed; 41 known optional
  import boundaries were classified.
- Public Python compile: 315 files passed.
- Public JSON parse: 428 files passed.
- Draft 2020-12 schema validation, public instance self-hashes, exact-environment
  `pip check`, branch diff, `git diff --check`, and public leak/private payload
  scans passed.

This is graph candidate evidence only. It does not establish causality, a confirmed relation, rule validity, anomaly performance, or GDN superiority. TASK-039D remains unauthorized.
