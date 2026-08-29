<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=e18dcc333c9374f6afd37d3c7c1b5bcce27b7a516e16befbd28c6894526100c1 authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# RCC Current Status

Scientific authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
Registry version: `0.1.0`
Registry snapshot: `2026-08-29T06:24:06Z`

## Current phase

**EVALUATION_SCOPE_EXPANSION**

Architecture implementation and pilot operation are complete. Scientific validation is partial; expanded evaluation and hypothesis validation remain incomplete.

## How to read status

- **Implemented / executed:** engineering state only.
- **Evidence-reviewed:** the backward-compatible component `audited` field; source or
  evidence status was reviewed against the pinned authority. This is not performance validation.
- **Result-integrity audited:** only explicit result-specific integrity artifacts; custody,
  immutability, ordering, and arithmetic checks. This is not scientific validation.
- **Independently reproduced:** an independent reproduction under required environment and custody.
- **Scientifically validated:** adequate independent evidence for a stated hypothesis; never
  inferred from component status and governed by `claims.csv`.

These counts are not a single completion percentage. An evidence-reviewed governance or
documentation component need not be a scientific executable, so Evidence-reviewed may exceed Executed.

## Component summary

- **Implemented:** 30
- **Executed:** 29
- **Evidence-reviewed:** 30
- **Independently reproduced:** 0

## Data / split audit

- **Dataset / process:** HAI 23.05 / P1 Boiler
- **Label access:** Normal construction is label-blind. D0 and D2 persist predictions before labels; D1 constructs a label-blind hashed object first but lacks a durable file-before-label gate.
- **Leakage:** NO VERIFIED LEAKAGE FOUND; two high qualifications are the D1 durable-ordering gap and test1-informed D2 V2 design.
- **Test1:** INNER development / 14-event pilot; not final validation
- **Test2:** One custody-level file access attempt was rejected before byte read; held-out result unavailable.

## Frozen D1 runtime / trace audit

- **Authority:** Frozen D1 uses the task-specific V4 authority plane: 42 CanonicalRuleDescriptorV4 descriptors, the frozen V4 evaluator bundle, the normal-only Utility V4 numeric resolver, and the committed one-attempt INNER grant.
- **Prediction:** 6,031 opportunity records, 788 anomalous rule records, 630 unique alarm decision seconds, and 626 downstream metric episodes.
- **Freeze:** SAFE_BUT_WEAKER_THAN_D0_D2; durable pre-label persistence = no.
- **Trace:** NON_EQUIVALENT; only the terminal outcome semantics partially overlap canonical RuntimeTraceV1.
- **Explanation:** A deterministic canonical RuntimeTraceV1 renderer exists, but frozen V4 D1 neither creates RuntimeTraceV1 nor calls that renderer; no frozen D1 explanation artifact exists.

## Frozen D2 fusion audit

- **Role:** Deterministic detector-preserving fusion-policy pilot
- **V1:** 11/14; Normal FAR 0.7056194750975128 episodes/hour; D0-miss recovery 0/3.
- **V2:** 11/14; Normal FAR 6.915070855955625 episodes/hour; D0-miss recovery 0/3.
- **D0 preservation:** VERIFIED_POINTWISE; D2(t)=D0(t) OR policy_admits_D1(t)
- **Freeze / labels:** V1 and V2 both use durable prediction-file-before-label gates.
- **Boundary:** V2 is test1-informed development, not independent confirmation. Current V1/V2 results do not establish that Detector-plus-Rule is generally useless.

## Components

| Component | Engineering / evidence display | Next action |
|---|---|---|
| DATA_PROVENANCE | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Rehearse public-safe restoration and verify timezone semantics on a fresh machine |
| SPLIT_GOVERNANCE | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Audit future entrypoints against split manifests and add a separately authorized D1 durable prediction gate |
| VARIABLE_ROLE_UNIVERSE | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Preserve frozen universe and review downstream profiling handoff in ARCH-003 |
| META_DISCOVERY | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Compare unique confirmed contribution and top-k sensitivity |
| STAT_DISCOVERY | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Measure split stability unique confirmed contribution and top-k sensitivity |
| GDN_DISCOVERY | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Validate seed and split stability unique confirmed contribution and pre-Top-5 masking impact |
| CANDIDATE_UNION | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Audit exact relation-profiling consumption in ARCH-003 |
| RELATION_PROFILING | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Compare criteria and stability without physical-truth claims |
| NUMERIC_AUTHORITY | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Keep values private and compare criteria in a new protocol |
| EVIDENCE_PACK | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Preserve the rendered-view boundary and inspect canonical handoff |
| RULE_DSL | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Audit canonical materialization and COMMON-42 authority bridge |
| T0_TEMPLATE | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Retain as preregistered comparator |
| T1_ONE_SHOT | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Reproduce under frozen provider policy before comparison claims |
| T1B_REPEAT | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Preserve budget equivalence in expanded comparison |
| T2_AGENTIC_FEEDBACK | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Design a comparable cohort that actually exercises feedback |
| DETERMINISTIC_VERIFIER | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Keep scientific and causal claims outside verifier authority |
| COMMON42_FREEZE | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Preserve exact authority bytes |
| RULE_RUNTIME | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Do not generalize fixed-runtime properties to future modes |
| SATISFACTION_TRACE | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Audit canonical-to-real trace representation in ARCH-006 and ARCH-008 |
| EXPLANATION_RENDERER | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Evaluate faithfulness separately from human usefulness |
| D0_PCA_SPE | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Add a stronger baseline only in a new preregistered study |
| D1_RULE_ONLY | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Expand utility evaluation without changing the frozen pilot |
| D2_V1 | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Retain as negative pilot evidence without tuning |
| D2_V2 | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Do not create result-driven V3 inside RCC |
| EPISODE_CONSTRUCTION | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Preserve the frozen episode policy |
| ATTACK_EVENT_RECALL | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Expand beyond the current 14-event pilot |
| NORMAL_FAR | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Treat D1 FAR as a primary operational risk |
| RESULT_INTEGRITY | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Keep integrity separate from validation and track the D1 durable-file ordering gap |
| OUTER_EVALUATION | BLOCKED | Require separate approval and preregistration before any held-out study |
| REPRODUCIBILITY | PARTIAL | Run a separately authorized fresh-machine rehearsal |
| PROFESSOR_REPORTING | CODE PRESENT · EXECUTED · EVIDENCE REVIEWED | Keep wording synchronized with RCC claims |
| THESIS_DRAFT | CODE PRESENT · NOT EXECUTED | Review all result wording against the checkpoint |

The compatibility field `claim_ready` is intentionally omitted from this headline. It means
only that a component supports at least one narrow implementation or contract claim.

## Experiments

| Experiment | Status | Result scope |
|---|---|---|
| EXP-01 | CODE PRESENT · COMPARISON NOT EXECUTED | Discovery artifacts exist; the comparative contribution experiment has not been performed. |
| EXP-02 | CODE PRESENT · COMPARISON NOT EXECUTED | Current references support deterministic execution but do not establish optimal criteria. |
| EXP-03 | EXECUTED · EVIDENCE-REVIEWED PILOT | One frozen construction cohort; validity and cost observations only. |
| EXP-04 | EXECUTED · EVIDENCE-REVIEWED PILOT | Single frozen 14-unit INNER pilot. |
| EXP-05 | CODE PRESENT · COMPARISON NOT EXECUTED | Implementation-level automated grounding evidence only. |
| EXP-06 | DESIGNED ONLY | No experimental outcome. |

## Authoritative claim view

Claim status comes only from `registry/claims.csv`.

| Claim | Status | Allowed wording |
|---|---|---|
| CLAIM-A | SUPPORTED_IMPLEMENTATION | The pinned HAI P1 INNER architecture and its frozen execution paths were implemented. |
| CLAIM-B | SUPPORTED_IMPLEMENTATION | The implemented pipeline transformed confirmed normal-data relation evidence into frozen executable rules under deterministic authority controls. |
| CLAIM-C | SUPPORTED_IMPLEMENTATION | The verifier deterministically checks the frozen structural evidence parameter split and operational contract. |
| CLAIM-D | SUPPORTED_IMPLEMENTATION | Given frozen rule numeric-reference authorization and input artifacts the current rule runtime evaluates without an LLM and produces deterministic traces. |
| CLAIM-E | UNVALIDATED | The frozen GDN arm contributed set-unique candidates; their unique scientific usefulness remains unvalidated. |
| CLAIM-F | NOT_SUPPORTED | The current pilot did not establish a feedback advantage and the feedback mechanism was not empirically exercised. |
| CLAIM-G | PILOT_ONLY | In the current 14-event INNER pilot D1 responded to three D0-missed events and D0 responded to one D1-missed event. |
| CLAIM-H | UNVALIDATED | Rule-only showed high event response and high normal false-alarm burden in the INNER pilot; practical utility remains unvalidated. |
| CLAIM-I | NOT_SUPPORTED | The two frozen D2 policies did not improve D0 attack-event recall in the current INNER pilot. |
| CLAIM-J | NOT_SUPPORTED | Held-out generalization remains unconfirmed because no OUTER scientific result is available. |
| CLAIM-K | CONDITIONAL | The implemented renderer is deterministically bound to frozen rule and trace information; comprehensive faithfulness remains to be evaluated. |
| CLAIM-L | UNVALIDATED | A trace-grounded explanation interface is implemented; human usefulness has not been evaluated. |
| CLAIM-M | NOT_SUPPORTED | The system records bounded temporal relation evidence and trace-grounded violations without causal attribution. |

## Research dimensions

- **Engineering:** Architecture substantially implemented; most frozen INNER paths executed.
- **Result integrity:** Explicit integrity audits exist for frozen D0, D1, D2 V1, and D2 V2 INNER results; this checks result custody and arithmetic, not performance validity.
- **Scientific validation:** Partial and incomplete; major performance and contribution hypotheses remain unvalidated or unsupported.
- **Reproducibility:** Fresh-machine independent reproduction remains pending.
- **Generalization:** Held-out generalization remains unconfirmed because no OUTER scientific result exists.
- **Claims:** Only narrow implementation or contract claims are supported; claims.csv is the authoritative claim view.

## Boundaries

Not established:

- GDN unique and stable scientific contribution beyond META and STAT
- Agentic verifier-feedback advantage
- Practical Rule-only operational utility
- Detector-plus-Rule improvement
- Held-out generalization
- Human explanation usefulness

## Exact next task

**ARCH-010 — Metrics / Episode Construction / Result Integrity Deep Audit**
