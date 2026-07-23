# Combined Prompt Fidelity

TASK-037D reconstructs the pinned `DetectionAgentV3` combined modes without
importing or executing ARGOS agents.

| Direction | System template | Target section | Contrast section |
|---|---|---|---|
| FN | `DETECTION_AGENT_V3_COMBINED_FN_PROMPT_TEMPLATE` | `##### DATA 0` | `##### NORMAL DATA 0 ` |
| FP | `DETECTION_AGENT_V3_COMBINED_FP_PROMPT_TEMPLATE` | `##### DATA 0` | `##### ABNORMAL DATA 0` |

Rows use exactly:

```text
value label index
DataFrame.to_string(index=False, header=False)
```

The prompt-source, DetectionAgent, dataset-loader and engine files are pinned
by SHA-256 in the task configuration. Each private request contains one target
and one matched contrast only. No previous rule, runtime error, detector
metric, TASK-037C result, extra formatting instruction, RepairAgent prompt or
ReviewAgent prompt is included.

The provider configuration changes no prompt bytes. It uses
`max_output_tokens: 6000`, omits temperature and seed, and adds no reasoning
parameter.
