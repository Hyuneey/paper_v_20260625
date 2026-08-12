# TASK-039E3-R1A Recovery Transport Timeout Authority Freeze

Status: `passed_task039e3_r1a_timeout_authority_freeze`

Authoritative E2 did not specify a concrete provider-call timeout duration.
It froze `timeout_before_response` as a retryable transport failure class, but
no numeric duration was present in the authoritative execution configuration
or retry policy.

TASK-039E3-R1A prospectively freezes `urlopen_timeout_seconds = 30.0` for
each transport attempt in a future authorized recovery execution. Its exact
operational meaning is the timeout argument in
`urllib.request.urlopen(request, timeout=30.0)`. It is not a total logical-call
deadline and is not a retroactive reinterpretation or correction of E2.

The historical E3 live implementation and the synthetic E2-PREP fixture both
used 30 seconds. Both remain non-authoritative supporting context; neither is
promoted into an original E2 fact.

The timeout applies uniformly to the recovery capability probe, T1, T1-B, T2,
and T1-DIRECT-NUMBER. T0 has no provider request. Retry authority remains two
transport retries, at most three attempts, fixed waits of 2 and 4 seconds,
and zero scientific-generation retries. A transport retry does not allocate a
new logical capability probe or scientific call.

Historical TASK-039E3 remains `blocked_task039e3_capability_gate`. Historical
TASK-039E3-R1 remains `blocked_task039e3_r1_recovery_implementation`.

No provider contact, credential access or presence check, capability probe,
scientific call, E1 private-evidence access, historical E3 private-root access,
or restricted-data access occurred. R1A authorizes only the next offline task,
`TASK-039E3-R1B_RECOVERY_IMPLEMENTATION`; provider contact, the recovery probe,
scientific execution, Rule v2, runtime, utility evaluation, and winner
selection remain unauthorized.

Five independent read-only audit lanes passed: Git/lineage/source integrity,
E2 timeout authority, historical 30-second context, R0/blocked-R1 bindings,
and boundary/contamination. Six offline test lanes also passed: R0 forensic
6/6, E2 authoritative configuration 8/8, R1A authority 6/6, three JSON
self-hashes plus five receipt bindings, public leak scan, and compile/pip/diff
hygiene. No lanes disagreed. Only the coordinator wrote authoritative files;
provider calls and private-custody writes were never parallelized or executed.
