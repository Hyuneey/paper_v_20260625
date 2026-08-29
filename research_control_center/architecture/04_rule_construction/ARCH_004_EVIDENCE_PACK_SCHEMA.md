# ARCH-004 Evidence Pack Schema

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

`RealConstructionEvidenceV1.render_view()` produces the exact construction view. It is a private, normal-only, authority-bound view; it is not a public result and grants no Rule v1 or runtime authority.

| Group | Field | Meaning and source | Normal-only | Numeric | Bound | LLM / T0 visible | Required |
|---|---|---|---|---|---|---|---|
| Relation facts | `relation_identity` | frozen confirmed direction identity | yes | no | relation hash | yes / yes | yes |
| Relation facts | `source`, `source_step_direction` | frozen source and step sign | yes | no | relation primitive | yes / yes | yes |
| Relation facts | `target`, `target_response_direction` | frozen target and response sign | yes | no | relation primitive | yes / yes | yes |
| Relation facts | `selected_delay_horizon_seconds` | frozen selected horizon | yes | yes | relation plus numeric reference | yes / yes | yes |
| Numeric authority | `numeric_bindings[10].value` | E1 construction-only values after projecting the selected horizon to its relation field | yes | yes | per-value reference and evidence identity | yes / yes | yes |
| Numeric authority | `numeric_bindings[10].reference` | immutable numeric reference returned by proposals | yes | no | hash | yes / yes | yes |
| Provenance | `approved_evidence_identities` | allowed E1 evidence identities | yes | no | ledger/cohort hashes | yes / yes | yes |
| Optional context | `semantic_process_metadata` | P1, relation family, approved construction status | yes | no | bounded key/value map | yes / yes | yes |
| Control | false boundary flags | raw HAI, labels, utility and candidate performance absent | yes | no | renderer validation | implicit in rendered view | yes |

E1 stores eleven roles: three relation-calibrated values, the selected horizon, and seven preregistered window constants. The E3 adapter projects the horizon to the fixed relation field and presents the other ten values plus references. Values are shown to the model so it can reason about the bounded proposal, but the strict output schema requires references and has no numeric-literal field. Public RCC files expose neither the private values nor private paths.

## Intentionally withheld

- raw HAI rows and private file paths;
- labels, attack intervals, test1 outcomes, utility metrics, D0/D1 predictions;
- candidate-arm performance or a META/STAT/GDN preference;
- cross-arm proposals and validity outcomes;
- runtime authority and canonical portfolio membership.

Support, consistency and effect summaries are not separately rendered to the construction model. Their authority survives through the confirmed relation, fit/confirmation references and numeric evidence bindings. Calling the view a free-form “evidence narrative” would therefore overstate what the model sees.
