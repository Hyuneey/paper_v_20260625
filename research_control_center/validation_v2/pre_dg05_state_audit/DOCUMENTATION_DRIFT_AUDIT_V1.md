# Documentation Drift Audit V1

This report records contradictions only; it does not repair them. Line numbers refer to the audited commit and may move later.

| Severity | Location | Current/stale text | Authoritative value / consequence |
|---|---|---|---|
| `SCIENTIFICALLY_MATERIAL` | `docs/project_state/CURRENT_STATE.json:5-17` | 2026-08-24, head `f1aa767…`, professor-first-results branch/next decision, local-only not pushed | Audit baseline is `a90d0e6`; V3 closure is frozen and exact reapproval is next. Mandatory entry document is stale. |
| `MISLEADING` | `docs/project_state/HANDOFF.md:21,58` | two obsolete next tasks | Current gate is V3 reapproval after resolving audit blockers. |
| `SCIENTIFICALLY_MATERIAL` | `research_control_center/START_HERE.md:10,24`; `SOURCE_AUTHORITY.md:7-13` | old `2dc7e6c…` described as sole authority | Valid historical PILOT pin, not sole current validation-v2 authority. |
| `SCIENTIFICALLY_MATERIAL` | `AGENTS.md:31,87,275`; `README.md:19,76` | primary Rule role FN correction; early TASK/GDN backend next | DEC-025 makes verified semantic Rule induction/governance primary; GDN is learned evidence, Fusion comparison. Historical constraints remain valid but current-phase language is stale. |
| `MISLEADING` | `research_control_center/validation_v2/START_HERE.md:28,31-32,42` | external compatibility unresolved; DG03 next; EXP04 next | External normal/T2 preparation and EXP04/05 are complete; V3 reapproval is current. |
| `MISLEADING` | `research_control_center/validation_v2/DECISION_GATES.md:7-8` | DG-03/DG-04 pending | Provider execution and DEC-025 DG-04 are complete. |
| `SCIENTIFICALLY_MATERIAL` | `research_control_center/validation_v2/PROGRAM_STATE.json:16,29,396,1252` | top-level/exact-next still DG05 V2 reapproval | V3 closure exists; exact V3 reapproval remains required. |
| `MISLEADING` | `PROGRAM_STATE.json:972,1045,1073` | older blocked/pending snapshots coexist as current-looking entries | Later completed states exist; selectors must distinguish historical snapshots. |
| `SCIENTIFICALLY_MATERIAL` | `docs/professor_experiment_update_v2/01_ONE_PAGE_SUMMARY.md:25`; `09_CLAIM_AND_LIMITATION_MATRIX.md:11` | Agentic benefit unsupported; DG-04 next | EXP-03B supports T2 versus T1-B only; T2 versus T0 not supported; DG-04 complete. |
| `MISLEADING` | `docs/professor_experiment_update_v2/04_EXP01_GDN_RESULTS.md:61-62` | provisional GDN-Assisted title; DG-04 pending | DEC-025 final working title is frozen. |
| `MISLEADING` | `docs/professor_experiment_update_v2/11_PROFESSOR_DECISION_AGENDA.md:161` | requests Executable V2 | Current candidate is V3, though audit is NO_GO. |
| `MISLEADING` | `docs/professor_experiment_update_v2/13_SLIDE_OUTLINE.md:90-91`; HTML `:768-769` | adjacent 228/146 statement followed by “72 cells, 12 scenarios, 3 results” | V3 rehearsal is 72 synthetic cells, 146 hypothetical scenarios, 228 typed surfaces. |
| `SCIENTIFICALLY_MATERIAL` | `13_SLIDE_OUTLINE.md:167`; HTML `:845` | scenario → eligibility → prediction freeze → lease | Frozen custody order is all predictions/freeze → lease → scenario/eligibility. Text reverses the leakage barrier. |
| `MISLEADING` | `research_control_center/validation_v2/TASK_INDEX.csv:10-17` | EXP-03 prepared; index ends before EXP-03B/xver/DG05 | Major completed stages absent. |
| `MISLEADING` | `research_control_center/SESSION_HANDOFF.md:25,51,235,244` | appended historical sections use current/next wording | Opening section is current; older blocks can be cherry-picked incorrectly. |
| `SCIENTIFICALLY_MATERIAL` | `research_control_center/validation_v2/exp03b/execution_v2/EXP03B_RESULTS_REPORT_V1.md:26` | “Frozen limitation: None” | Independent QA and DEC-025 impose T0, abstain, normal-reference, and lexicographic-burden limitations. |
| `MISLEADING` | `research_control_center/history/decisions/DEC-025-final-method-and-scoped-agentic-contribution-lock.md:34` | current relevance says external custody/provider not ready | These stages subsequently completed; DG-05 V3 readiness is now the issue. |
| `SCIENTIFICALLY_MATERIAL` | `docs/thesis/THESIS_MASTER_OUTLINE_V1.md:62,82,90,111,120,125,129` | old GDN candidate role, 42-direction cohort, no utility/runtime results, negative old T2 narrative | Historical thesis outline conflicts with DEC-025 and later results if reused as current. |
| `SCIENTIFICALLY_MATERIAL` | `research_control_center/history/PROJECT_TIMELINE.md:276` | “14 independent INNER events” | Current EXP-04 authority calls these contiguous development units and does not assert independence. |
| `MISLEADING` | `dg05_metric_verifier_closure/PUBLIC_PRIVATE_DG05_METRIC_CLOSURE_INDEX_V1.json` | QA report byte hash `71c977…` | Actual `INDEPENDENT_QA_V2.md` bytes hash `f7de1c…`; 14 of 15 total indexed byte hashes matched and one differed. Ancillary index drift, not V3 manifest self-hash failure. |
| `MISLEADING` | `FINAL_METHOD_LOCK_V1.json` T0 role | `STRONG_SAME_INFORMATION_DETERMINISTIC_BASELINE` | Frozen T0 receipt says STAT/GLOBAL GDN not consumed; T2 consumed them. “Same information” needs a field-consumption caveat. |

## Status-language findings

The principal `CURRENT_CONTEXT.md` appropriately says validation is partial, generalization unconfirmed, and fresh-machine scientific reproduction incomplete. The RCC status model correctly distinguishes design, implementation, integration, execution, evidence review, result-integrity audit, reproduction, and scientific validation. Drift arises where historical documents use “current,” “complete,” “validated,” or “next” without a date/authority boundary.

Specific cautions:

- `COMPLETE` for normal-only construction does not mean attack-validated.
- `CONFIRMED` relation means frozen normal evidence, not causal or physical ground truth.
- `REPRODUCTION AUDIT` on HAI22 train6 does not prove fresh-machine end-to-end reproduction.
- `228/228` means declared identifier coverage, not complete upstream provenance.
- V3 `CLOSURE_FROZEN` does not mean user-approved or production-routable.

## Professor-feedback chronology boundary

The feedback lineage itself warns that May reframing is user-confirmed context, July dates are repository decision dates rather than proven delivery dates, August 18/26 are internal update preparation, and package preparation does not prove professor approval. The project history should preserve these distinctions.
