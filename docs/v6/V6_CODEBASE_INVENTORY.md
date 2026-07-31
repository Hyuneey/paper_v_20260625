# V6 Codebase Inventory

## Method

The inventory uses only paths returned by `git ls-files`, checks every path
against an explicit public-root allowlist, and parses source with AST without
importing project modules.

Production public-symbol scope is `src/paperworks/**/*.py`. Tracked tests and
TASK-030/032 fixtures provide boundary evidence but do not enter the production
public-symbol count. Frozen ARGOS source is outside the rerun read allowlist
and is classified from committed aggregate documentation only.

Machine-readable source:
`docs/task_reports/TASK-039P0_PUBLIC_SYMBOL_INVENTORY.json`.

## Recomputed Counts

| Item | Count |
|---|---:|
| Production Python modules | 51 |
| Production public symbols | 727 |
| Existing schemas | 7 |
| TASK-030/032 contract fixtures | 67 |
| Tracked public test files inspected | 180 |
| New or unresolved virtual components | 12 |

| Module classification | Count |
|---|---:|
| `canonical_v6_core` | 8 |
| `reusable_with_v2_adapter` | 15 |
| `legacy_read_only` | 18 |
| `engineering_support` | 8 |
| `unresolved_research_decision` | 2 |

## Static Findings

Canonical contracts do not import primary legacy DSL/verifier/runtime packages.
However, `contracts.__init__`, `verifier_v1`, `runtime_authority`, and
`vertical_slice_v1` import `phase1_adapters`. P1 must remove canonical runtime
and verifier reliance on that compatibility adapter.

`paperworks.gdn.torch_backend` imports torch unconditionally, and package-level
GDN import reaches it. V6 callers must use the masked producer directly until
the fidelity and optional-import decision is resolved.

SWaT-era markers remain in twelve production modules spanning loaders,
historical orchestration, evaluation, profiling defaults, and smoke text. The
JSON inventory records exact public paths and lines. No HAI implementation is
present under `src/`.

Paths matching a prohibited root or token were excluded before access.
