# RepairAgent Safety Protocol

The TASK-038A adapter preserves the audited RepairAgent role while removing the
unbounded retry loop and host execution used by upstream ARGOS.

## Eligibility

Repair is permitted only for the 13 TASK-037D static-valid rules whose terminal
runtime state is:

- `target_runtime_failed`
- `contrast_runtime_failed`
- `output_contract_failed`

Provider failures, absent responses, static-invalid rules, and executable rules
are not repair candidates.

## Request boundary

The private future request may include the current rule, a sanitized runtime
error, the failing generation value-only chunk, the required
`inference(sample)` signature, and the pinned ARGOS Repair system prompt.
Generation labels, metrics, inner or outer data, sealed-test data, and
TASK-037E results are prohibited.

The system prompt is loaded from the read-only ARGOS commit
`6b24161ff08de069840a1fb4fbaecf7bf8e393f1` only after the source file hash is
verified. The source is parsed as an AST constant and is not imported.

## Output gate

A future Repair output must pass extraction, syntax, the frozen static policy,
target and contrast container runtime, output shape, finiteness, and binary
domain checks. A failed revision receives no retry and cannot be reported as
repaired.

## Execution boundary

Generated code is never loaded on the host. Future checks use the established
rootless Podman boundary with no network, non-root identity, read-only root,
dropped capabilities, no new privileges, and bounded CPU, memory, PIDs, and
time. Containers receive values only.
