# Portfolio Freeze

The frozen runtime portfolio is the factory-replayed `UtilityProtocolV4CanonicalAuthority`: exactly 42 ordered `CanonicalRuleDescriptorV4` records, one `CanonicalFullCensusPlanV4`, 420 relation-role runtime references and one numeric-authority descriptor. The selected horizon remains descriptor-bound rather than a private registry row.

Freeze checks cover exact dataclass types, relation membership/order, semantic preimages, descriptor hashes, reference-set cardinality, main portfolio identity `COMMON-42`, T2 exclusion, full-census policy and final authority hash. The evaluator adds factory custody and exact semantic replay; D1 adds a committed one-attempt execution grant. A caller cannot substitute a portfolio, descriptor, relation, numeric registry or execution scope.

The public freeze contains identities and metadata, not private numeric values. Reproducibility means deterministic reconstruction and identity checking under the frozen source and private custody; fresh-machine reproduction remains incomplete.
