# ARGOS Component Evidence Ledger

## Scope

TASK-038F uses only committed aggregate reports from TASK-033 through
TASK-038E. It did not read private rules, prompts, responses, values, labels,
or prediction arrays and did not execute a provider, agent, detector, rule,
outer reader, or sealed-test reader. Exact report hashes and source fields are
registered in
[`TASK-038F_EVIDENCE_SOURCE_MAP.json`](../task_reports/TASK-038F_EVIDENCE_SOURCE_MAP.json).

## Evidence Ledger

| Component | Frozen evidence | Interpretation |
|---|---|---|
| Isolated rule runtime | TASK-033 passed eight executions over four synthetic fixtures without performance metrics | Frozen rule execution can be deterministic under isolation |
| Original one-shot generation | 100 calls produced 84 responses, 61 static-valid rules, and 55 executables | One-shot generation is operational but yield-sensitive |
| Output-budget remediation | 100 calls produced 100 static-valid and 91 executable rules; combined cohort 146 | Output budget materially affected extraction and execution yield |
| One-rule validation | Precision 0.8462, recall 0.1886, point F1 0.3084 | A precise rule can still have narrow anomaly coverage |
| Multi-rule validation | Best-1 F1 0.4801; Top-3 OR F1 0.5360 at 105.56 FP/10k; coverage-heavy arms exceeded 2,000 FP/10k | More rule coverage can increase false alarms sharply |
| Detector provenance | LSTMAD family recovered; Alpha/Beta identity unresolved | Both variants must remain co-primary |
| Generic diagnostic fusion | Best-1 and Top-3 max fusion increased macro point F1 for both variants | Generic rules and detector predictions can be complementary |
| Error-conditioned cohort | 96 registered, 83 executable: 51 FN and 32 FP | Detector-error-conditioned rule generation is feasible |
| Repair operability | 13/13 failures recovered under one revision and no retry | Strong bounded runtime-recovery evidence |
| Review inner effect | 77 calls; 72 improved, one equal, three regressed, one invalid | Strong inner-only refinement evidence |
| Repair utility | Four useful, four equal, five regressive; two selected in A1 | Repair is not a performance optimizer |
| Review outer transfer | All 19 selected reviewed rules transferred positively relative to parent | Strong descriptive transfer among selected reviewed rules |
| Full A3 robustness | A3 minus A0: Alpha -0.0218, Beta +0.0364 | Complete branch effect is variant-mixed |
| FP safety | 19 selected FP rules: four safe, 14 costly, 14 harmful, one ineffective | FP correction requires explicit TP/event guards; categories overlap |
| Efficiency | 90 unique calls, 404,399 provider-reported tokens | Agent value must be weighed against bounded but material cost |

## Headline Branch Results

The values below are macro direct PA-free outer point F1 from the previously
exposed follow-up partition.

| Variant | Detector | A0 Full | A1 Full | A2 Full | A3 Full |
|---|---:|---:|---:|---:|---:|
| LSTMADalpha | 0.3541 | 0.4884 | 0.4544 | 0.5047 | 0.4666 |
| LSTMADbeta | 0.4233 | 0.3880 | 0.3895 | 0.4215 | 0.4245 |

A2 improved over A0 for both variants. A1 was mixed and largely unchanged or
worse. A3 was mixed relative to A0. These observations do not select a final
branch or detector variant.

## Evidence Limits

- The exact ARGOS KPI LSTMAD Alpha/Beta identity remains unresolved.
- The outer partition was previously exposed before the Repair/Review program.
- The project used a leakage-corrected split, bounded revisions, direct PA-free
  metrics, and a secure project-owned runtime.
- No sealed ARGOS confirmation has been executed.
- These records do not validate the proposed multivariate CPS method.
