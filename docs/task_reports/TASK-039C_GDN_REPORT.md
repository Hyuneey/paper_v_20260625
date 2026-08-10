# TASK-039C-GDN Upstream-Aligned Candidate Discovery

Status: `blocked_optional_dependency`

Phase A verified the pinned upstream commit and all seven P1D-frozen Git blob and SHA-256 identities. The dedicated backend is classified `upstream_aligned_validated`; the existing deterministic and Torch/PyG project trainers remain synthetic smoke only.

The arm stopped at the dependency gate. No already-approved environment contained both exact project-pinned dependencies (`torch==2.12.1`, `torch-geometric==2.8.0`). No install, upgrade, version guess, fallback backend, or HAI access occurred.

No seed was attempted, no candidate was evaluated, and no top-10/20/40 or ranking was produced. BR2 pair supervision, META/STAT outputs, train3, train4, test, labels, attacks, attention-primary ranking, and post-hoc XAI were not used.

Fidelity receipt hash: `93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4`.
Dependency environment fingerprint: `698ed2cc888a36415c0bce0fbf78f69c073af5e917da35dc1174c49871c68304`.

## Verification

- GDN fidelity, candidate-contract, artifact, schema, and leak-scan tests: 19 passed.
- C0, P1D, BR0, BR1, and BR2 regressions: 157 passed across the appropriate CPython 3.12 and 3.14 environments.
- Guarded tracked-test discovery: 572 runnable tests passed; 40 known optional import boundaries were classified (`jsonschema`: 22, `pytest`: 16, `torch_pyg`: 2), with zero unexplained imports, failures, or errors.
- TASK-032 was exercised through guarded discovery. Direct CPython 3.14 execution was not accepted because that installed environment lacks the optional JSON Schema date/date-time format packages; no dependency was installed to force it.
- Both installed Python environments reported `pip check` clean. Repository compile and GDN JSON/schema/self-hash checks passed.
