# Runtime Rule Engine Contract

## Boundary

Runtime is a project-owned deterministic interpreter. It loads accepted JSON
DSL only, has no provider dependency, and does not import planning or LLM
modules.

Before evaluation it verifies schema/version, rule hash, accepted verifier
result, parameter IDs/versions/hashes, input variables, sampling alignment, and
operating regime.

## Operators

Only versioned trigger, lag, window, relation-family, tolerance, persistence,
abstention, and output operators are available. There is no dynamic expression,
function loading, Python evaluation, shell, or plugin execution surface.

## Runtime behavior

- Preserve input-to-output alignment.
- Emit ordered satisfaction steps.
- Support deterministic abstention.
- Reject hash, schema, or version mismatch.
- Do not generate natural-language explanation.
- Record exactly which parameter values and hashes were used.

## Output

`schemas/runtime_trace_schema.json` defines execution/rule/verifier/window IDs,
status, trigger and expected-effect state, violation and score, abstention,
satisfaction trace, parameter values, alignment confirmation, and timestamp.

An `evaluated` trace is not a benchmark result. It is an execution record for a
specific accepted rule and input window.
