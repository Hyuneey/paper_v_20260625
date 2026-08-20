# TASK-039E3-R2R-UTILITY-INNER-AUTHORIZATION-CODE-MATERIALIZED-HAI-RECOVERY-V1

Execution mode: one coordinator for every sensitive operation. Read-only agents
may inspect public Git state only. No manual user path input is required.

## 0. Purpose

Recover the INNER execution authorization after the operational
`LOCAL_BINDING_INPUT_REQUIRED` blocker. Replay continuity, verify the frozen
official HAI acquisition authority, materialize only `hai-test1.csv` and
`label-test1.csv` in a private Codex cache, validate exact hashes and sizes,
persist only the ignored local HAI binding, recover existing MAIN/supplement
bindings path-silently, perform the audited preflight once, issue the existing
D1 INNER authorization once, update continuity, and stop before D1 execution.

## 1. Exact repository lineage

- Repository: `Hyuneey/paper_v_20260625`.
- Branch:
  `task-039e3-r2r-utility-inner-authorization-code-materialized-hai-recovery-v1`.
- Base: `586267b1cee6ec949c32624c5a156618588ff98a`.
- Preserve R3 base `1a961eadc4813acfc959580c0558f0bf33aa5c7c`,
  Contract A `f95ab2a1969b36b53aba5bb2053844f8724664c1`, Audit B
  `66a8f2a39ac6cc0365d405ce28a5d04d522ba898`, initial blocker
  `ce7abfa8f1a5f59ea9e846e808eaaaad3e0cfde8`, continuity bootstrap
  `bf5284da64e33fd056beac71d56d187f715f3b48`, local helper
  `1d00e1abe1e081fa905f7d500a1752a271208895`, and base commit above.
- Require exact clean HEAD/index, no rebase, main update, unrelated merge, or
  lineage rewrite.

## 2. Continuity replay

Read in exact order: `AGENTS.md`, `START_HERE.md`, `CURRENT_STATE.json`,
`HANDOFF.md`, `RESEARCH_SCOPE.md`, `AUTHORITY_INDEX.md`,
`SAFETY_BOUNDARIES.md`, `TASK_LEDGER.md`, relevant authorization tasks, and
latest sanitized blockers. Validate the current-state self-hash. Git receipts
win over chat memory.

## 3. Durable design correction

Append `DEC-DATA-001`: a fresh environment may reconstruct the HAI INNER
payload from the pinned official acquisition authority. Local cache paths are
disposable machine state; official source, pinned commit, exact allowlist, and
SHA-256 identities are authority.

## 4. Frozen acquisition authority

Use only `https://github.com/icsdataset/hai` at
`2a814cebc9a66b06c9e5cd545e2d72e65d383737`, edition `hai-23.05`. Moving
refs, mirrors, archives, user uploads, alternate versions, and unofficial
sources are prohibited. Official GitHub and required official Git-LFS
endpoints/redirects are the primary route.

## 5. Exact authorized INNER payload

- `hai-23.05/hai-test1.csv`: SHA-256
  `78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be`,
  size 31,255,559 bytes.
- `hai-23.05/label-test1.csv`: SHA-256
  `eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc`,
  size 1,242,017 bytes.

No other payload is required.

## 6. Test2 seal

Do not materialize, open, hash, parse, or scientifically inspect any test2
payload or attack information. Pinned public Git tree/pointer metadata is
allowed only where unavoidable. Require test2 LFS fetches, opens, hashes, and
scientific parses to remain zero.

## 7–8. Private cache and path silence

Create/reuse a deterministic private cache outside this repository. Never
print or publish its path, home path, clone destination, HAI binding, registry,
or locator. Do not display environment values, private working directories,
resolved paths, private listings, tracebacks, exception strings, or subprocess
commands containing destinations. `PRIVATE_PATHS_EXPOSED = 0`.

## 9–10. Materialization helper and Git strategy

Create `scripts/local/materialize_hai_inner_payload_v1.py` with no private
path. It is non-interactive, suppresses Git/LFS path-bearing output, enforces
the official origin and pinned commit, limits acquisition to the two authorized
files, validates hashes/sizes, and emits fixed sanitized fields only. Clone
with automatic LFS smudge disabled. Use explicit per-file LFS fetches; never use
unrestricted pull/fetch-all or whole-dataset checkout.

## 11–12. Git-LFS and frozen fallback

Check `git lfs version` path-silently and report only availability. If selective
LFS cannot be used, use only the already-audited TASK-039AR official Kaggle
distribution fallback when its committed metadata and byte-equivalence
receipts replay exactly and each file can be downloaded selectively without
test2. Otherwise block `CODE_MATERIALIZATION_BLOCKED_GIT_LFS_UNAVAILABLE`.

## 13–15. Cache validation, custody, and output

Reuse an existing cache only after exact origin, commit, file hash, and size
validation. Reject noncanonical cache state. Raw-byte hash only the two
authorized files; never parse. Any mismatch blocks
`CODE_MATERIALIZATION_BLOCKED_TEST1_CUSTODY_MISMATCH`. Success output is limited
to materialization PASS, official source/commit, LFS availability, two
materialized/hash/size booleans, zero test2 LFS fetches, and zero path output.

## 16–17. Local binding

After materialization, bind the private cache internally as `HAI_DATA_ROOT` and
persist it only in ignored `.env.custody.local` using the approved format.
Require ignored true and tracked false. Preserve approved existing MAIN and
supplement registry/locator bindings from the file or process environment;
never blank them, display them, or copy unrelated variables/secrets.

## 18. Public materialization documentation

Append `DEC-DATA-001` and update `LOCAL_PRIVATE_BINDING_GUIDE.md` to describe
both approved routes: hidden input for existing local data, and pinned official
code materialization. Include no absolute path.

## 19. Synthetic tests

Add `tests/test_task039e3_r2r_hai_inner_materialization_v1.py` with no network
or real data. Cover source and pinned revision enforcement, test1-only policy,
test2 exclusion, hash/size mismatch, redaction, outside-repository cache,
valid-cache reuse, noncanonical rejection, and ignored binding persistence.

## 20. Materialization Commit M

Before network, commit only helper, synthetic tests, public documentation
updates, and this task. No HAI, `.env`, or private path. Suggested message:
`TASK-039E3-R2R add reproducible HAI INNER materialization recovery`.

## 21. Static gate

Before network run materialization tests, local bootstrap tests, frozen
authorization contract and independent suites, compileall, pip check, and diff
check. Require 37/37 authorization tests, 109/109 invalid attacks rejected, and
accepted invalid zero. Contract A, Audit B, and R3 stay byte-identical.

## 22–23. One real official materialization

After Commit M and static PASS, run the helper once with network restricted to
the official GitHub/LFS route or frozen official selective fallback. Record
sanitized official Git and per-file acquisition counters. Test2 payload,
scientific parsing, event derivation, rules, and metrics remain zero.

## 24. Resume authorization in this task

After HAI binding succeeds, continue without user interaction. Load only
approved keys from `.env.custody.local` internally and merge them into the
controller environment without displaying values.

## 25. Immutable authorization contract

Do not change the authorization V1 source or its two test files. Contract A is
`f95ab2a1969b36b53aba5bb2053844f8724664c1`; Audit B is
`66a8f2a39ac6cc0365d405ce28a5d04d522ba898`. Do not create V2.

## 26. Private binding recovery

Use existing MAIN/supplement registry and locator bindings. If a registry is
bound but its locator is absent, inspect only immediate regular non-symlink JSON
siblings, path-silently, validate exact locator identity and target, and require
exactly one match. If both bindings are absent, block with the authority-specific
fixed code. Never scan HOME, recurse, display a path, or regenerate authority.

## 27–28. Expected private authorities

MAIN binds descriptor
`665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928`,
reference set
`d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae`,
420 references, registry
`9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0`,
and locator
`b5588c04d08d88d4ee2a2d319708e62d10bc04330baeb7591876f076270e4ac4`.

Supplement binds descriptor
`d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927`,
reference set
`5139cae6e454318f0ca4317f3f5eaa5f775bd4f75261c4110ea610815929b580`,
6 references, registry
`12ec7f50a953e097cd7cbe3ac93c7cabfb669130612d7f30ab3b19df85289aaf`,
locator
`8c11872dca6a0c8b2544c2988dd57c969ddc036f51b04578d936fdc3a60757ac`,
and purpose `CROSS_SOURCE_ISOLATION_EVENT_CENSUS_ONLY`.

## 29–31. Static gate and sole real preflight

Require exact R3/A/B, all static attacks rejected, exact HAI binding, ready
private bindings, zero paths, and zero test2 payload access. Call existing
`perform_inner_execution_custody_preflight_v1()` exactly once; do not
reimplement or retry. Require all six expected hashes, test2 false, scientific
parsing false, and zero private exposure.

## 32–33. Exact authorization

After preflight PASS, call `issue_inner_execution_authorization_v1` once and
validate it with `require_real=True`. Exact scope is
`HAI_23_05_P1_TEST1_COMMON42_D1_RULE_ONLY_INNER_V1`: COMMON-42 and 42 relations;
D1 true; T2, D0, D2, detector, fusion, OUTER, test2, recalibration,
regeneration, and metric modification false.

## 34. No scientific execution

Feature/label parsing, source/attack derivation, rule execution, metrics,
detector, and real utility remain zero. This task stops before D1.

## 35–37. Reports, leak scan, and Authorization Freeze A2

After PASS create seven self-hashed sanitized materialization, preflight,
authorization, readiness, bundle, receipt, and Markdown reports with the exact
task prefix. They contain no paths, rows, label content, private values,
registry payload, or attack interval. Run a silent leak scan and require
`LEAK_SCAN_PASS`. Commit only these reports as Authorization Freeze A2 with
message `TASK-039E3-R2R issue INNER D1 authorization from pinned HAI materialization`.

## 38–39. Continuity and Commit B2

Update current state, authority index, ledger, handoff, and decision log.
Record strategy `PINNED_OFFICIAL_SOURCE_REPRODUCIBLE_CACHE`, authorization
issued true, D1 executed false, no cache path, and next task
`TASK-039E3-R2R-UTILITY-INNER-D1-EXECUTION-V1`. Commit only project-state files
as B2 with message
`TASK-039E3-R2R update handoff after code-materialized INNER authorization`.

## 40. PASS status and flags

PASS status is
`passed_task039e3_r2r_utility_inner_authorization_code_materialized_hai_recovery_v1`.
Set INNER authorized and D1 authorization issued true; D1 executed, OUTER
authorized, and `REAL_UTILITY_EXECUTION_AUTHORIZED` remain false.

## 41. Block conditions

Block for unavailable official network, unavailable LFS with no exact fallback,
missing pinned commit, wrong origin, payload mismatch, accidental test2 fetch,
path disclosure, missing/mismatched private authority, contract regression,
scientific execution, or leak-scan failure. Never ask the user for a path or
terminal action. Emit only the sanitized blocker and STOP.

## 42. Exact next task after PASS

Do not start automatically. The next task is
`TASK-039E3-R2R-UTILITY-INNER-D1-EXECUTION-V1`, the first real utility
execution. It consumes this exact authorization, uses only authorized test1 and
private authorities, executes COMMON-42 D1, computes frozen metrics, keeps
test2 sealed, makes no result-driven change, and stops for integrity audit.

## 43. Final response

Return only the requested sanitized lineage, acquisition, custody, static,
counter, authorization, hash, state, blocker, and exact-next-task fields; then
STOP.
