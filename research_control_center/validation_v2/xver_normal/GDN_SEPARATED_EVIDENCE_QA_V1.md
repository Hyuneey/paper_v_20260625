# Separated evidence role binding: independent scoped QA

Verdict: **PASS_SCOPED_ROLE_BINDING_AND_ADAPTER_QA**.

Read-only independent reviewer replayed all 15 synthetic tests. An initial
mutable-inner-row defect was fixed before freeze; both evidence types now
reject mutable nested rows. The actual frozen EXP03B projector/render path is
called by a global-only adapter: exactly 20 structural rows and five global
GDN rows. Auxiliary typed input and an added auxiliary argument fail closed.
Frozen T0 and train2 verifier reject auxiliary objects. Three-seed medians,
signed effects, unavailable states and train1/train2 separation are preserved.

No provider calls, credentials, private data, attack values, or scientific
training were used for this QA. Independent agents made no writes.

This is not full scientific execution readiness. The remaining execution
adapter must bind SCI01 event-source provenance and each seed's exact purged
partition, replay external custody, prove inference-kernel equivalence, freeze
the environment and performance preflight, and keep global/event outputs in
separate artifact namespaces. No claim of 12-run completion or frozen provider
budget follows from these synthetic tests.
