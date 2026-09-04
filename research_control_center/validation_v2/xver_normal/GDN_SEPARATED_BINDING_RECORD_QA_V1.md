# Approved-role binding and record synchronization QA

Scope: user scientific binding decision, typed global/event separation,
global-only adapter into the frozen provider projector, and current records.
Verdict: **PASS_SCOPED_BINDING_RECORD_SYNC**; not complete external execution.

- Independent replay: binding/status self-hashes, 11 implementation hashes,
  six upstream identities; 15 helper/adapter tests and five current-gate tests.
- Coordinator focused context/projection/role tests: 34 PASS.
- EXP03B regression: 95 PASS (mock transports only; no real provider calls).
- Validation V2 bundled environment: 458 tests, PASS, 14 optional skips.
- Additional CUDA-environment Validation V2 attempt: 458 tests, one dependency
  error and eight skips. Historical EXP01 test requires exact CPU torch version
  identity and rejects the separate CUDA build. No environment or historical
  test was altered to force that attempt green. This is not a scientific run.
- RCC/UI: 214 PASS. Registry/generated/privacy validation PASS, exposure zero.
- Git whitespace validation PASS. Frozen EXP01C/EXP03B kernels, Stage-A,
  core V2A authorities, and historical blocked audit artifacts unchanged.
- Exact new source allowlist entry is the binding commit
  `a207dceecd1903705af904624e8e7289c9f4b036`, not an arbitrary mutable ref.

The initial mutable-inner-row issue was corrected before the binding freeze.
Provider global aggregation cannot accept the auxiliary evidence type. The
actual frozen projector emits 20 structural rows and five global GDN rows;
auxiliary injection and auxiliary input to T0/verifier are rejected.

Current status deliberately remains
`BINDING_APPROVED_EXECUTION_INTEGRATION_PENDING`: scientific runs 0/12,
execution_active=false, no external T0 portfolio, no exact provider pack or
token/cost freeze. The scientific role choice is resolved. Version-aware
execution/custody/partition adapters and preflight still precede scientific
runs. This is remaining implementation work, not a request for another user
decision about the approved roles.

Provider/credential/test/attack/excluded-label-value access this continuation:
zero. No private numeric artifacts were read or generated. Existing private
vault manifest remains unchanged; no additional backup claim is made.

No task/integration push or merge: the parent scientific task has not reached
full preparation PASS. DG-XVER-PROVIDER remains unapproved/not ready, DG-05
NOT_APPROVED, and the professor package NOT_SUBMITTED.
