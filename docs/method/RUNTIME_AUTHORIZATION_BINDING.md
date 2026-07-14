# Runtime Authorization Binding

## Authority Boundary

DEC-043 permits execution only through an immutable
`RuntimeAuthorizationBundleV1`. Accepted rules, verifier results, external
artifact collections, and TASK-032D outcomes remain individually
runtime-unauthorized.

Authorization revalidates the accepted rule's verification-subject hash, the
accepted verifier-result self-hash and deterministic ID, verifier policy, graph
and evidence hashes, the exact parameter ID/hash set, and all verified
reference sets. Dataset, regime, source, and target bindings must agree.

## Receipt

The receipt records the accepted rule, verifier result, graph, evidence,
parameters, verifier policy, synthetic runtime scope, and caller-supplied
creation time. Its SHA-256 excludes only `authorization_hash`. Its deterministic
`AUTH-*` ID excludes the ID and self-hash fields.

Receipt integrity and the full verifier binding are rechecked immediately
before every execution. A manually constructed bundle lacks the internal
authorization capability, and a modified authorized bundle fails the pre-run
recheck.

The receipt is project-owned orchestration metadata. `runtime_authorized` is a
non-serialized bundle property and is not added to any canonical TASK-030
artifact.
