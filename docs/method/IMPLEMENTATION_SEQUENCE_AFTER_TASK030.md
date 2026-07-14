# Implementation Sequence After TASK-030

TASK-031 authorizes none of these steps automatically.

| Order | Proposed task | Independently reviewable result | Gate |
|---|---|---|---|
| 1 | TASK-032A | Standard Draft 2020-12 schema registry plus explicit legacy adapter skeleton and synthetic mapping report | DEC-035 dependency approval |
| 2 | TASK-032B | Delayed-response DSL v1 dataclasses and serializers only | TASK-032A review |
| 3 | TASK-032C | Parameter and evidence adapters for `LAG`, `TOL`, `DURATION`, `SUPPORT` | TASK-032B review |
| 4 | TASK-032D | MVP-required deterministic verifier stages | TASK-032C review |
| 5 | TASK-032E | LLM-free runtime trace and separate explanation record | TASK-032D review |
| 6 | TASK-032F | Synthetic delayed-response vertical-slice integration | TASK-032E review |

The smallest next task is TASK-032A. It must not add DSL behavior or execute a
rule. It should add the approved validator dependency, validate existing
TASK-030 synthetic fixtures, and define an adapter that reports unsupported
legacy inputs without conversion. DEC-035 remains proposed, so TASK-032A is not
started by this report.
