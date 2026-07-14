# Deterministic Vertical-Slice Replay

`verify_task032f_deterministic_replay()` performs two fresh complete runs from
the same serialized fixtures and configuration. The second run does not reuse
the first run's accepted rule, verifier result, authorization capability,
runtime trace, or explanation object.

Replay requires equality of:

- every adapter target hash;
- candidate transport and verification-subject hashes;
- accepted-rule hash;
- verifier-result identifier and self-hash;
- authorization identifier and receipt hash;
- scenario execution, trace, explanation identifiers, and hashes;
- final report hash.

All configured fixture byte hashes are captured before the first run and after
the second run. Any difference fails closed. Configuration mappings are hashed
canonically, so source mapping order does not alter results.

The replay result establishes deterministic synthetic plumbing only. It does
not establish stability on real data or across learned graphs, calibrators,
rules, providers, hardware, or scientific datasets.
