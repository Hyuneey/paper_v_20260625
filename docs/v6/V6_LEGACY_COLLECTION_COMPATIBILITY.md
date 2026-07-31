# V6 Legacy Collection Compatibility

`DelayedResponseArtifactCollectionV1` remains unchanged for TASK-032
historical fixtures and replay.

`LegacyDelayedResponseCollectionAdapterV1` delegates the original graph,
evidence, parameters, lookups, and authority flags through the bounded
collection protocol. It does not reserialize, rewrite, or replace any legacy
artifact.

The canonical verifier and runtime-authority modules depend on the protocol,
not the Phase-1 concrete class. Legacy adapter and vertical-slice modules may
continue importing `phase1_adapters`.

Compatibility gates preserve:

- accepted Rule v1 authority hash;
- verifier-result self-hash;
- runtime-authorization receipt hash;
- TASK-032F deterministic replay hash.

The legacy anomaly/event-anchored evidence remains valid only for its original
scope. It is not normal-only v6 evidence.
