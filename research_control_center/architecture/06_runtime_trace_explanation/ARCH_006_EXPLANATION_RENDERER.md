# Explanation renderer audit

## What exists

`paperworks.contracts.explanation_v1.render_delayed_response_explanation` is a deterministic, template-based canonical renderer. It accepts an authorized canonical runtime bundle, `RuntimeExecutionOutcomeV1`, and `DelayedResponseRuntimeWindowV1`. It revalidates authorization, trace hash/schema, rule, verifier, window, graph, evidence, normal-reference, and parameter-hash bindings.

It calls no LLM and no network service.

## Frozen D1 relationship

The frozen V4 D1 execution does not import or call the renderer and emits task-specific trace hashes rather than `RuntimeTraceV1`. No tracked adapter maps the frozen D1 result into the canonical explanation contract. Therefore explanation generation was not part of the frozen D1 result path.

## Fidelity boundary

| Check | Status | Evidence |
|---|---|---|
| source/target match | IMPLEMENTED_CANONICAL_ONLY | copied from the authorized canonical rule after trace binding |
| direction and relation match | PARTIAL_CANONICAL_ONLY | fixed canonical text and violation type; not tested on frozen V4 D1 |
| horizon/lag match | IMPLEMENTED_CANONICAL_ONLY | authorized lag bounds are copied; observed lag is explicitly prohibited |
| numeric provenance | IMPLEMENTED_CANONICAL_ONLY | parameter references and hashes are rebound; raw parameter values are not improvised in prose |
| PASS/FAIL/ABSTAIN consistency | IMPLEMENTED_CANONICAL_ONLY | canonical trace state selects fixed observed text and result fields |
| final outcome match | IMPLEMENTED_CANONICAL_ONLY | violation and abstention fields are trace-derived |
| no new variable | IMPLEMENTED_CANONICAL_ONLY | variables are copied from the accepted rule |
| no new number | PARTIAL_CANONICAL_ONLY | lag bounds are authorized; prose uses no caller-authored number; comprehensive corpus testing is future EXP-05 |
| no causal/root-cause claim | IMPLEMENTED_CANONICAL_ONLY | parser rejects either claim flag and templates avoid causal wording |
| input-change consistency | FUTURE_EXP05 | no formal frozen-D1 condition-change experiment exists |

## Scientific boundary

The canonical renderer has structural fidelity tests and deterministic fixtures. This supports an implementation claim only. It does not establish human usefulness, operational usefulness, causal interpretation, or corpus-wide explanation faithfulness. Human usefulness remains `UNVALIDATED`.
