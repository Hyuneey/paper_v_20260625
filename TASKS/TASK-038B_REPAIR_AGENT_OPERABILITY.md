# TASK-038B: ARGOS RepairAgent Bounded Operability Experiment

TASK-038B executes one source-aligned, no-retry Repair revision for each
reproducibly failed member of the frozen thirteen-rule TASK-037D Repair
population.

The experiment uses two commits:

1. implementation, failure replay, and exact call-manifest freeze;
2. aggregate provider, static, runtime, drift, branch, and operability results.

Raw rules, prompts, responses, values, predictions, errors, receipts, and
runtime files remain under ignored private storage.

ReviewAgent, detection metrics, inner execution, outer access, fusion, and
sealed-test access are prohibited.

Final status: `passed_repair_agent_operability_experiment`

All thirteen initial failures were reproducible. Thirteen one-shot Repair calls
produced thirteen static-valid revisions, and all thirteen passed deterministic
target and contrast runtime contracts. This is an operability result only.
