# Claim–Evidence Matrix V1

| ID | Claim | Classification | Evidence | Required boundary |
|---|---|---|---|---|
| A | Verifier-guided feedback improves LLM semantic Rule induction relative to T1-B. | `SUPPORTED` | EXP-03B exact set 17/29 vs 10/29; paired-only 8:1; 10 distinct train3-confirmed exact-repair pairs | Frozen normal-only protocol; matched **maximum** call budget; not attack utility |
| B | T2 outperforms deterministic T0. | `NOT_SUPPORTED` | T0 exact 18/29 vs T2 17/29; T0 higher principal pair/directional metrics | Must appear as mandatory limitation |
| C | GDN provides supporting learned-graph evidence. | `SUPPORTED` | EXP-01C retained learned predictive/functional evidence; GLOBAL5 used in T2 construction | Noncausal; no admission authority |
| D | GDN is primary discovery authority. | `PROHIBITED_CLAIM` | META+STAT are frozen candidate authority; GDN unique convertible pairs 0 | GDN cannot admit/rank candidates |
| E | The Rule system detects anomalies. | `PARTIALLY_SUPPORTED` | V2A Rule-only 11/14 on HAI23 test1 development, with 37.6095 false episodes/hour | Current T0/T2 portfolios remain attack-unvalidated; development only |
| F | Rule response adds detector recovery. | `PARTIALLY_SUPPORTED` | Development Rule responded on some PCA misses, but frozen Fusion recovered 0 | Rule response is not Fusion recovery; held-out recovery remains `PENDING_DG05` |
| G | PCA+Rule improves detector performance. | `NOT_SUPPORTED` | EXP-04 Recall unchanged and +2 false episodes for frozen V2A Fusion | Future T0/T2 Fusion evidence remains `PENDING_DG05`; new portfolios are not retroactive evidence |
| H | The method transfers across HAI versions. | `PARTIALLY_SUPPORTED` | Normal-only HAI22/21 construction completed; partial GDN contexts; separate portfolios frozen | Attack portability/generalization remains `PENDING_DG05`; no IID pooling |
| I | Explanations are structurally trace-grounded. | `SUPPORTED` | EXP-05 6,418/6,418 fidelity units passed 11 checks | Structural fidelity only |
| J | Explanations are useful to humans. | `NOT_SUPPORTED` | No human study or user outcome | Explicitly unvalidated |
| K | The learned graph is causal. | `PROHIBITED_CLAIM` | GDN evidence is predictive/functional only | No causal design or ground truth |
| L | The system is production-ready. | `PROHIBITED_CLAIM` | portfolios are held-out candidates; DG-05 unexecuted; P0 executable blockers | No operational deployment validation |
| M | The V3 metric surface is complete. | `SUPPORTED` for identifier coverage | expected/builder/verifier each 228 with exact set equality | Does not imply complete upstream provenance or real results |
| N | DG-05 V3 is ready for immediate real execution. | `NOT_SUPPORTED` | current manifest requires reapproval; audit finds routing/coordinate/census/oracle blockers | `NO_GO` until separately closed |
| O | 146 scenarios form one primary sample. | `PROHIBITED_CLAIM` | no-pooling policy; versions/morphologies differ | version-specific primary results only |
| P | HAI21 T2’s 2 Rules / 1 pair is an implementation error. | `NOT_SUPPORTED` | frozen normal-only lineage/QA | Treat as portability outcome without rescue |

## Claim hierarchy

The strongest current empirical thesis statement is the scoped development claim in A. The work may also claim a functioning normal-only construction/governance pipeline and structural trace fidelity. It may not yet claim held-out attack utility, Agentic superiority over T0, causal discovery, human usefulness, or production readiness.
