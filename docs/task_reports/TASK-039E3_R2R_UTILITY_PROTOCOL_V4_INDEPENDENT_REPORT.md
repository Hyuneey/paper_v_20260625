# TASK-039E3 R2R Utility Protocol V4 Independent Audit

Status: `blocked_task039e3_r2r_utility_protocol_v4_independent_audit`

The independent public-only oracle reconstructed the lower COMMON, numeric-reference, feature-schema, and regression authorities without opening the private registry or any HAI file. It executed 116 adversarial cases: 99 invalid forms were rejected and 17 invalid forms were accepted. Production V4 and its implementation test were not modified.

## Finding disposition

| Historical finding | Independent result | Evidence |
|---|---|---|
| T2 exact portfolio membership unbound | CLOSED | Four T2/fake-membership requests rejected; V4 main plan remains COMMON-42. |
| Opportunity semantic identity unchecked | OPEN | A self-consistent caller timestamp/row-time substitution was accepted. |
| Full-census numeric reference authority unbound | CLOSED | Exact 420-reference set replayed; 20 numeric/reference substitutions rejected. |
| Canonical full-census provenance bypass | OPEN | Empty, singleton, caller-selected 39-relation, and one-row 42-relation opportunity sets received census hashes. |
| Serialized feature schema authority substitution | CLOSED for semantic membership | Eleven semantic/schema substitutions rejected; evaluator 12/10/22 and COMMON 9/10/19 replayed independently. |
| Canonical scalar type policy not enforced | OPEN | Eight nested tuple-to-list substitutions remained authoritative through the top-level V4 validator. |
| Target terminal-state provenance unbound | OPEN | Self-rehashed target/source window substitutions, an interior split-boundary claim, and a caller-selected response outcome were accepted. |
| Regression component authority hash mismatch | CLOSED | The three lower artifacts replayed exactly; six mutated/historical substitutions rejected. |

## Regression results

- V4 implementation: 51/51 passed.
- V3: 27/27 passed.
- V1/V2: 40 passed, 2 intentional private-custody skips, 42 run.
- Normal-only public/synthetic: 106/106 passed.
- `compileall`, `pip check`, and `git diff --check`: passed.

## Access and claim boundary

Private numeric values, the private registry, HAI normal/test data, labels, attack intervals, providers, API keys, scientific LLMs, and network resources were not accessed. Utility was not executed. The result does not authorize evaluator implementation or execution.

Four blockers remain. No remediation was performed in this audit.
