# Contract Artifact Hash Policy

TASK-032C defines one self-hash policy for graph, evidence-package, and
parameter-registry artifacts.

1. Deep-copy the artifact mapping.
2. Remove only the top-level `artifact_hash` field.
3. Serialize as UTF-8 JSON with sorted keys, compact separators, ASCII
   escaping, and `allow_nan=false`.
4. Calculate SHA-256 and compare or populate the top-level field.

Nested hashes remain part of the digest. NaN and positive or negative infinity
fail closed. Caller mappings are never modified.

The self-hash proves document integrity only. It does not approve scientific
content, bind a rule, create a verifier result, or authorize runtime use. This
policy does not change TASK-032B, whose canonical rule document hash covers the
complete serialized rule document.
