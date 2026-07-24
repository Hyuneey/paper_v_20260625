# ARGOS Final Claim Matrix

| Claim | Supported? | Evidence | Required qualifier | Prohibited stronger wording |
|---|---|---|---|---|
| LLM rules can be generated | Yes | TASK-035A/AR and TASK-037D funnels | Under frozen provider, prompt, budget, and audit contracts | LLM rules are reliably generated in general |
| Frozen rules can execute deterministically | Yes | TASK-033, TASK-037D, TASK-038B/C/E replay | For audited rules in the isolated runtime | Arbitrary generated Python is safe |
| RepairAgent can recover runtime failures | Yes | TASK-038B recovered 13/13 | One bounded revision for this static-valid cohort | Repair always fixes generated code |
| RepairAgent improves detection performance | Mixed, not established as a general effect | TASK-038E: four useful, four equal, five regressive | Repair is an operability mechanism; utility requires reselection | Repair optimizes rule performance |
| ReviewAgent improves inner performance | Yes | TASK-038C: 72 improvements among 77 calls | Inner-only, direct PA-free, one revision | Review guarantees generalization |
| Review improvements can transfer to outer | Yes, descriptively | TASK-038E Review transfer | Previously exposed outer follow-up | Confirmed out-of-sample superiority |
| Selected Review rules all transferred positively in this study | Yes | 19/19 selected reviewed rules positive versus parent | This frozen selection and exposed outer partition | Every reviewed rule generalizes |
| Repair+Review is superior to one-shot | No, mixed | A3-A0 negative for Alpha and positive for Beta | Branch effect depends on unresolved detector variant | A3 is the final winner |
| Full Aggregator is superior to detector-only | Mixed | TASK-037E and TASK-038E branch tables | Depends on branch, detector variant, KPI, and metric | Aggregation always improves detection |
| FP correction safely removes false positives | No | 14 harmful and 14 costly classifications among 19 selected FP rules | Overlapping categories; TP and true-event removal must be reported | FP correction is safe after Review |
| ARGOS is exactly reproduced | No | TASK-037A and project adaptation boundaries | Paper-aligned, leakage-corrected component reproduction | Exact ARGOS reproduction |
| ARGOS methodology is partially supported | Yes | V1-V7 component judgments | Descriptive outer evidence pending sealed confirmation | ARGOS is fully validated |
| Proposed multivariate method is validated | No | No proposed-method experiment in this track | ARGOS evidence informs design only | SWaT method effectiveness is established |
| Sealed-test superiority is established | No | Sealed test never accessed | Requires explicit joint preregistration and authorization | Final or confirmed superiority |
