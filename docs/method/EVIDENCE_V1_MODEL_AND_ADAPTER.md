# Evidence v1 Model and Phase 1 Adapter

`EvidencePackageV1` represents anomaly-anchored evidence through immutable
window references, a matched normal reference, candidate lag, selection policy,
claim boundaries, and artifact hashes. It contains no raw sequence values.

Registry-first parsing verifies the self-hash and checks window/lag ordering,
source-target separation, raw-value exclusion, all three prohibited claims,
exact-regime matching, and a pre-registered deterministic policy that does not
use label performance.

The Phase 1 adapter accepts serialized RelationProfile and RelationEvidencePack
mappings. It requires matching source, target, and profile IDs and supports only
the binary-actuator to continuous-sensor delayed-response path. Legacy
`calibration_normal` is mapped explicitly to `calibration`.

Window references, matched normal context, regime, policy, and hashes are
external required context. Trigger/response arrays and raw values are never
copied or reconstructed. Aggregate support omitted by the closed target schema
is declared as information loss in the adapter result.
