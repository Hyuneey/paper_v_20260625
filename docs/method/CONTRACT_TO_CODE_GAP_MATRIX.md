# Contract to Code Gap Matrix

TASK-031 is a static compatibility audit at commit
`317a43a0bfe0be59caad611edf895c0f3ddc6e37`. It makes no production or
dependency changes.

| Contract artifact | Existing implementation | Classification | Semantic difference and risk | Migration action | Expected task | Compatibility |
|---|---|---|---|---|---|---|
| Graph | `CandidateUniverseArtifact`, `CandidatePair` | `reuse_with_wrapper` | universe membership is not a directed attributed graph | wrap as pre-ranking nodes/eligible edges | 032C | preserve IDs/hashes |
| Graph | `GDNEdgeArtifact`, `GDNEdgeRecord` | `reuse_with_wrapper` | ranked learned edges omit full semantics/uncertainty | join only to registered universe edges | 032C | never convert score to causal claim |
| Evidence package | `RelationProfile`, events | `reuse_with_wrapper` | strong support aggregates, but raw event lists and no matched-normal IDs | create non-reconstructive v1 references | 032C | legacy profile remains read-only |
| Evidence package | `RelationEvidencePack` | `adapt_in_place_later` | lacks event anchor, regime, matched normal and policy hash | implement adapter, do not mutate stored pack | 032C | explicit loss report |
| Parameter registry | `CalibrationRecord` | `reuse_with_wrapper` | lacks approval, stability, uncertainty and complete lineage | map limited roles; status cannot exceed evidence | 032C | synthetic smoke never approved |
| Parameter registry | v1 registry | `new_implementation_required` | no current registry artifact | implement typed records/reference resolution | 032C | version 1.0.0 |
| Rule DSL | `RuleAst` and three predicates | `deprecate` for new creation | embedded resolved numbers, no regimes/evidence/graph refs | retain legacy parser; explicit adapter only | 032A/032B | legacy read-only |
| Rule DSL | `RuleSchemaRegistry` | `reuse_with_wrapper` | custom one-family semantics, not standard JSON Schema | separate structural registry and semantic checks | 032A/032D | no silent acceptance widening |
| Verifier result | `VerificationReport`, `FeedbackIssue` | `reuse_with_wrapper` | two statuses and empirical checks; missing verified references and repairability | preserve legacy result, create v1 result | 032D | deterministic authority retained |
| Runtime trace | `RuntimeFiringRecord`, `RuntimeEvaluation` | `replace_later` | firing-centric aggregate, no abstention/satisfaction trace/hash binding | new v1 trace emitted by adapted engine | 032E | legacy runtime remains callable for legacy artifacts |
| Explanation record | `RuntimeExplanation` | `deprecate` | mixes facts, semantics, and formatting | split trace, record, renderer | 032E | no causal wording |

## Existing Strengths to Preserve

- Candidate membership is created before GDN Top-K ranking.
- Candidate self-edges are prohibited and message-passing self-loops are kept
  separate.
- Profiling and calibration use operation-specific split guards.
- Numeric parameters originate from calibration records, not planners.
- The verifier is deterministic and final for Phase 1.
- Runtime is deterministic and LLM-free.

## Principal Gaps

The largest gaps are cross-artifact identity/provenance, standard schema
validation, typed graph/evidence/parameter records, complete verifier-stage
coverage, accepted-result binding, abstention and structured satisfaction
traces. Similar names do not remove these semantic gaps.
