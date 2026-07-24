# ARGOS Methodological Validity Report

## Overall Assessment

The frozen evidence supports `partial_methodological_support`. One-shot rule
generation, Repair runtime recovery, Review inner refinement, and selected
Review outer transfer all produced meaningful component evidence. The complete
Repair-plus-Review branch was not robust across the unresolved LSTMAD variants,
FP correction frequently removed true-positive or true-event evidence, and no
sealed confirmation exists.

This is a **paper-aligned, leakage-corrected component reproduction**, not an
exact ARGOS reproduction.

## Component Judgments

| Dimension | Support label | Basis |
|---|---|---|
| V1 One-shot generation operability | `partial_component_support` | Generation and deterministic execution work, but yield and coverage are variable |
| V2 Repair operational validity | `strong_component_support` | 13/13 runtime failures recovered under one bounded revision |
| V3 Repair detection utility | `partial_component_support` | Four useful, four equal, five regressive; only two survived A1 selection |
| V4 Review inner effectiveness | `strong_component_support` | 72 improvements among 77 calls; 76 deterministic executables |
| V5 Review outer transfer | `strong_component_support` | All 19 selected reviewed rules transferred positively; evidence is descriptive outer validation |
| V6 End-to-end A3 robustness | `partial_component_support` | A3 versus A0 was negative for Alpha and positive for Beta |
| V7 Safety and efficiency | `partial_component_support` | Runtime containment was strong, but FP safety and token cost remain material |

## Substantive Conclusion

ARGOS의 핵심 아이디어 전체가 무효한 것은 아니다. RepairAgent는 실행
불가능한 규칙을 복구하는 역할에서 강한 유효성을 보였고, ReviewAgent는
열등한 detector-rule 조합을 inner에서 개선했으며 선택된 reviewed rule의
개선은 outer에서도 모두 parent 대비 양의 방향으로 전달되었다. 그러나
Repair가 복구한 규칙의 탐지 효용은 혼합되어 있었고, 완전한
Repair-plus-Review branch는 LSTMADalpha와 LSTMADbeta에서 일관된 F1
개선을 보이지 않았다. 또한 Review를 거친 FP rule도 다수의 true
positive와 anomaly event를 제거했다. 따라서 현재 증거는 ARGOS의
구성요소별 유효성을 지지하지만, 전체 agentic Aggregator의 일반적
우월성을 지지하지는 않는다.

## Why Rules Correct Rather Than Replace the Detector

ARGOS가 LLM rule을 단독으로 쓰지 않고 detector 보조 신호로 사용한
이유는 낮은 평균 rule 성능만이 아니다.

1. One-shot rules often have narrow coverage, so rule-only replacement is weak.
2. The detector supplies broad baseline coverage.
3. FN rules can add missed anomaly evidence through `max(detector, FN_rule)`.
4. FP rules can remove false alarms through `min(detector, FP_rule)`, but can
   also remove true positives.
5. Review improved many rules but did not eliminate correction risk.
6. Every direction therefore requires an explicit no-op candidate.
7. Detector-preserving directional correction is structurally justified, not
   merely a workaround for low average rule performance.
8. The Full Aggregator is not universally superior and must remain guarded.

## Was the Extended Reproduction Meaningful?

The extended reproduction was scientifically useful because it separated the
effects of one-shot generation, Repair, Review, detector baseline, FN/FP
correction, no-op selection, and Full Aggregator composition.

- One-shot generation was operationally possible but variable.
- Repair provided strong execution recovery.
- Review provided strong inner improvement and substantial descriptive outer
  transfer.
- Detector aggregation helped in some branches but was not universally
  superior.
- FP correction was high-risk without TP-removal constraints.

It is not exact reproduction because the KPI LSTMAD Alpha/Beta identity remains
unresolved, the split is project-owned and leakage-corrected, agent revisions
are bounded, execution uses a project-owned secure runtime, Review and
selection use direct PA-free metrics, the upstream driver is incomplete, and
sealed confirmation has not run.

## Component Roles

RepairAgent should be treated as an operability and contract-recovery
mechanism, not as a performance-improvement agent. A repaired candidate must
return to deterministic validation and no-op-aware selection.

ReviewAgent can be retained as a training-time candidate-refinement mechanism,
but it must not be the final authority. Its feedback must remain inner-only,
bounded, provenance-complete, and subordinate to deterministic validation and
direction-specific safety guards.

## Final Boundary

The outer partition is previously exposed descriptive follow-up validation.
No branch or detector variant is selected as a final winner. No claim of final
performance, confirmed superiority, proposed-method validity, or sealed-test
improvement is supported.
