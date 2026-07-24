# TASK-038A: ARGOS Repair/Review Agent Factorial Protocol and Safety Freeze

Status: `passed_agent_factorial_protocol_freeze`

TASK-038A freezes the complete 96-slot TASK-037D population into 384 A0/A1/A2/A3
logical branch records. It implements deterministic branch states, source-hash
verified Repair/Review prompt adapters, inner-only Review regression evidence,
split guards, private-artifact schemas, a mock-only provider surface, future
metrics, and a maximum 192-call no-retry budget.

No real provider call, Repair, Review, rule execution, inner-label execution,
outer access, or sealed-test access occurred. TASK-037D rules and TASK-037E
selections remain unchanged.

Future execution requires separate TASK-038B through TASK-038H authorization.
