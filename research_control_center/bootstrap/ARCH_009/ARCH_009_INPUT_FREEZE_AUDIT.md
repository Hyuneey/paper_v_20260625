# Input, freeze and label audit

V1/V2 validate frozen D0/D1 bytes, hashes, row closure, source mapping and
policy-specific authorities. No raw features, D0 scores, labels or scientific
reruns enter fusion. Both output 54,000 self-hashed records and enforce atomic
temporary write, flush/fsync, replace, readback validation and a frozen-state
gate before label access.

Classification: `D2_DURABLE_GATE_VERIFIED`. This is stronger than the original
D1 shallow in-memory gate, but cannot retroactively strengthen D1's historical
custody boundary. Integrity is hash/state-gate based, not physical OS
immutability or external signature.
