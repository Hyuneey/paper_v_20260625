# Thesis Result Claim Matrix

This matrix is frozen after the utility path stopped before label access. The
construction classifications A-H must not change during thesis writing.

## Construction claims

| ID | Claim | Status | Direct evidence | Thesis-safe wording | Prohibited wording |
|---|---|---|---|---|---|
| A | Bounded pipeline feasibility | **SUPPORTED** | T0, T1, and T1-B accepted 42/42; T2 accepted 39/42 | The bounded evidence-bound pipeline produced verifier-admissible rules for confirmed relations in this 42-relation cohort. | The rules improved anomaly detection. |
| B | One-call T1 feasibility | **SUPPORTED** | 42 calls, 42 structured proposals, 42 admissible proposals, 42 accepted relations | One frozen T1 call yielded an admissible proposal for every relation in this cohort and realized run. | LLMs reliably construct valid CPS rules generally. |
| C | Repeated-sampling robustness | **PARTIALLY_SUPPORTED** | T1-B recovered one first-draw rejection on call 3 and tolerated one unrelated parse failure, using 84 calls beyond the first-draw budget | Repeated sampling provided limited stochastic robustness at three times T1's call cost. | Best-of-three generally improves validity or provider reliability. |
| D | T2 validity improvement | **NOT_SUPPORTED** | T2 accepted 39/42; feedback eligibility and all feedback/recovery actions were zero | Incremental validity benefit of T2 was not observed, and feedback recovery was not empirically exercised. | Verifier feedback improved construction or was experimentally validated. |
| E | T2 efficiency advantage | **NOT_SUPPORTED** | T2 and T1 each used 42 calls, but accepted 39 and 42 relations; T1-B used 126 calls for 42 | T2 did not improve the observed construction-validity/call frontier. | T2 provides the best efficiency-quality trade-off. |
| F | Deterministic calibration rationale | **SUPPORTED** | All Direct-number outputs were structured, yet normalized errors remained large | Schema validity did not imply numerical accuracy; normal-data deterministic calibration is supported for this contract. | LLMs cannot estimate numeric parameters in any setting. |
| G | Deterministic no_rule safety | **SUPPORTED** | Three unsupported-variable proposals became `no_rule`, not accepted rules | The deterministic verifier/controller prevented three invalid proposals from entering the accepted set. | `no_rule` guarantees deployed safety or anomaly utility. |
| H | Candidate-origin effect | **INCONCLUSIVE** | Overlapping META/STAT/GDN memberships; GDN N=5 | Origin summaries are exploratory; no material origin effect was established. | META, STAT, or GDN origin causally determines success. |

## Labeled utility claims

| ID | Question | Execution status | Allowed conclusion |
|---|---|---|---|
| U1 | Do admissible proposals have anomaly-detection utility? | **NOT_EXECUTED** | Utility was not evaluated. |
| U2 | Does utility distinguish T0, T1, and T1-B? | **NOT_EXECUTED** | No utility distinction was measured; their frozen executable projections were also identical. |
| U3 | Does T2 `no_rule` create a coverage/false-alarm trade-off? | **NOT_EXECUTED** | Only construction-admission safety was observed. |
| U4 | Does T1-B repeated sampling change downstream utility? | **NOT_EXECUTED** | Only generation robustness and call cost were observed. |
| U5 | Do LLM structural choices add utility beyond T0? | **NOT_EXECUTED** | No downstream utility or distinct executable projection supports this claim. |
| U6 | Does utility justify construction cost? | **NOT_EXECUTED** | Costs may be reported descriptively; no cost-utility winner is allowed. |

`NOT_EXECUTED` must not be rewritten as failed utility, negative utility, null
utility, zero utility, or a not-supported empirical hypothesis.

## Primary contribution boundary

The smallest defensible contribution statement is:

> A governed, evidence-bound rule-construction framework that separates
> bounded proposal generation from deterministic normal-data calibration,
> deterministic validity admission, explicit `no_rule` handling, and
> downstream utility authority; evaluated through a controlled
> construction-validity comparison on 42 confirmed HAI P1 relation
> directions.

Empirically supported components are construction feasibility, bounded
one-call feasibility, limited repeated-sampling robustness, deterministic
invalid-proposal exclusion, the negative T2 result, the validity ceiling, and
the calibration rationale. Strict validity/utility separation, bounded
feedback architecture, and intended LLM-free execution are methodological
design contributions, not demonstrated downstream performance.

## Abstract claim inventory

The final abstract remains deliberately unwritten.

### Allowed claims

- A governed, evidence-bound construction pipeline was evaluated on 42
  confirmed HAI P1 relation directions.
- T0, T1, and T1-B achieved 42/42 verifier acceptance; T2 achieved 39/42.
- One-call T1 feasibility was observed for this cohort and run.
- T1-B recovered one first-draw rejection at three times T1's call cost.
- T2 emitted three fail-closed `no_rule` outcomes; its feedback path was not
  exercised and no incremental validity benefit was observed.
- Direct-number normalized errors support deterministic normal-data
  calibration for the frozen contract.
- Utility was not evaluated.

### Unsupported claims to delete

- demonstrated anomaly-detection, detector, or utility performance;
- T2 or agentic superiority;
- empirically validated feedback recovery;
- general LLM construction reliability or general best-of-three benefit;
- candidate-origin superiority, causal discovery, or root-cause evidence;
- production runtime, Rule v2, deployment, or full-system safety validation;
- any construction, utility, or cost-utility winner.

### Material qualifications

- one HAI 23.05 P1 cohort and 42 confirmed directions;
- one provider/model snapshot and realized stochastic run;
- a three-arm deterministic-validity ceiling;
- an unexercised T2 feedback path;
- overlapping origin groups and GDN membership N=5;
- no labeled utility, detector integration, or production runtime result;
- a post-result utility protocol that remained unaudited, with execution
  intentionally stopped before label access.
