# TASK-039E3 R2 Failure Forensic Audit

Status: `passed_task039e3_r2_failure_forensic_audit`

## Finding

The corrected capability gate passed in one attempt. The first scientific call, T1 relation index 0 local call 1, then received an HTTP 400 response. Frozen V3 correctly classified `http_400` as non-retryable and terminated with `completed_nonretryable_transport_failure` after one scientific attempt.

The exact frozen request was reconstructed from the single authorized relation-0 E1 record. Its canonical request hash, `4a0e54d4ef9723e9232ec7a7b51cf40e6680bf614c85cab07e0f8d848cf614e6`, exactly matches authoritative scientific custody. The request matches the frozen endpoint, model, prompt, schema, sampling, and serialization contract.

This proves deterministic local construction and custody coherence. It does not prove which provider-side condition caused HTTP 400. The frozen transport did not retain an HTTP error body, error code, message, or parameter. Therefore the supported root-cause category is `FROZEN_REQUEST_HTTP_REJECTION`; narrower attribution would exceed the evidence.

## Custody and partial science

Disk-authoritative `HEAD.json` reconstruction found exactly one capability record and one scientific provider record, with no orphan or pending records. Public and private ledger heads match. The partial proposal/outcome/direct counts of 1/1/0 correspond solely to the completed T0 result for relation 0. No T1 proposal or T1 outcome was committed; T1-B, T2, and direct-number did not start.

The failure is not `no_rule`, a negative scientific result, or evidence of arm underperformance. No arm comparison, utility comparison, or winner selection is valid.

## Authority boundary

The failed run is not authorized for retry or resume. Capability probe accounting is already at the maximum cumulative count of two; a third probe is prohibited. The consumed R2 Authorization V3 is not reusable authority. A future protocol may be designed, but any provider contact or scientific reexecution requires a separate offline design, independent audit, and new authorization freeze.

Recommended next task: `TASK-039E3-R2-SCIENTIFIC-RECOVERY-PROTOCOL`.

## Data boundary

This audit contacted no provider, inspected no credential or environment-key presence, executed no runner, and performed no scientific call. Coordinator-only read access was limited to 11 named private files and one relation-0 E1 record needed for request-hash reconstruction. No raw request, provider body, E1 numeric value, proposal text, credential, authorization header, chain-of-thought, or sensitive private path is included in this report.
