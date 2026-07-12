# ARGOS Prompt Fidelity Audit

TASK-025 reconstructs the pinned ARGOS `train-LLM-only` DetectionAgentV3 prompt
path for one selected KPI chunk. It does not call a real provider, execute
generated Python, run RepairAgent or ReviewAgent, run full ARGOS training, or
report benchmark performance.

Pinned ARGOS commit:

```text
6b24161ff08de069840a1fb4fbaecf7bf8e393f1
```

## Paper-Code Prompt Mapping

| ARGOS component | Pinned file/function | Reproduced field | Deviation |
|---|---|---|---|
| Detection Agent system prompt | `agent/prompts/detection.py::build_detection_agent_v3_prompt` | `system_prompt` | Template literal is read by AST instead of importing ARGOS to avoid provider/client side effects. |
| `train-LLM-only` mode selection | `driver.py --mode` default and `runtime/engine.py::Engine(... mode="train-LLM-only")` | `mode` | Only the first DetectionAgentV3 request is reconstructed; RepairAgent and ReviewAgent are not run. |
| sample serialization | `agent/detection_agent.py::DetectionAgentV3.run`, `curr_df.to_string(index=False, header=False)` | `user_prompt` | Chunk selection is deterministic first eligible chunk, not `np.random.randint(0, 1000)`. |
| chunk-size resolution | `driver.py --chunk_size default=1000`; `runtime/engine.py::Engine(chunk_size=1000)` | `chunk_selection.chunk_size` | No CLI override is used in TASK-025. |
| expected Python code fence | `agent/prompts/detection.py` default V3 prompt | `response_capture.code_extracted` | Captured response is validated but never executed. |
| required signature | prompt text and `agent/agent.py::Agent.extract_code` | `response_capture.static_safety.signature` | TASK-025 validates exactly one `inference` function with AST. |
| normal-rule comments | `agent/prompts/detection.py` default V3 prompt | `system_prompt` | No deviation. |
| abnormal-rule conditions | `agent/prompts/detection.py` default V3 prompt | `system_prompt` | No deviation. |
| iteration history behavior | `agent/detection_agent.py::DetectionAgentV3.run` appends `##### CODE FROM LAST ITERATION` when present | `iteration_history` | First capture uses no previous rule, so no history block is appended. |

## Fidelity Notes

- `DetectionAgentV3.__init__` builds its system prompt with
  `build_detection_agent_v3_prompt(self.chunk_size, mode)`.
- For `train-LLM-only`, `build_detection_agent_v3_prompt` falls through to
  `DETECTION_AGENT_V3_DEFAULT_PROMPT_TEMPLATE`.
- `DetectionAgentV3.run` serializes each dataframe with
  `to_string(index=False, header=False)` and prefixes it with `##### DATA {i}`.
- The upstream run loop samples chunks using `np.random.randint(0, 1000)`.
  TASK-025 intentionally replaces that with a predeclared deterministic first
  eligible chunk rule so the prompt capture is reproducible and not
  performance-selected.
- The upstream prompt asks for a Python code fence and
  `inference(sample: np.ndarray) -> np.ndarray`. TASK-025 captures and
  statically validates that shape but does not execute the code.

## Boundary

This is an ARGOS rule-only prompt-capture smoke. It is not a benchmark result
and must not be used as a thesis performance claim.
