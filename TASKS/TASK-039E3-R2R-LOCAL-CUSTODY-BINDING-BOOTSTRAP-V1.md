# TASK-039E3-R2R-LOCAL-CUSTODY-BINDING-BOOTSTRAP-V1

## TWO-LAYER-CONTINUITY-UPGRADE

Execution mode: single coordinator. No multi-agent private path handling.

## 0. Purpose

The preceding path-silent authorization recovery correctly stopped with
`RECOVERY_BLOCKED_MISSING_HAI_DATA_ROOT` and status
`blocked_task039e3_r2r_utility_inner_execution_authorization_v1_path_silent_recovery`.
This was not a scientific, evaluator, authorization-contract, or custody-hash
failure. The authorization contract remains valid: 37/37 static tests passed,
109/109 independent invalid attacks were rejected, and accepted invalid is 0.
No custody preflight, private-authority access, HAI access, scientific parsing,
or D1 authorization occurred.

This task establishes a durable local-only, path-silent binding layer for
machine-specific custody bindings. It does not issue INNER authorization, run
custody preflight, or execute D1.

## 1. Repository and exact base

- Repository: `Hyuneey/paper_v_20260625`.
- Branch: `task-039e3-r2r-local-custody-binding-bootstrap-v1`.
- Exact base: `51f9378ea50a5a779a8d75bdd5ab8634330f23bc`.
- Require exact HEAD, clean worktree/index, no rebase, no main update, and no
  unrelated merge.
- Replay latest blocker `RECOVERY_BLOCKED_MISSING_HAI_DATA_ROOT` and confirm D1
  authorized, D1 executed, and `REAL_UTILITY_EXECUTION_AUTHORIZED` are false.

## 2. Read continuity first

Before work, read in order: `AGENTS.md`, `START_HERE.md`,
`CURRENT_STATE.json`, `HANDOFF.md`, `SAFETY_BOUNDARIES.md`, recent
authorization task specifications, and the sanitized recovery blocker report.
Validate the current-state self-hash. Git state, not chat memory, is authority.

## 3. Current safe recovery condition

Establish the HAI data-root environment binding, then begin a new path-silent
authorization recovery task. Do not retry the failed attempt in the same
coordinator context, infer or search for the HAI path, recover it from logs or
history, or start D1.

## 4. Two-layer continuity design

Layer A is Git-tracked `docs/project_state/`. It contains only public research
status, decisions, task lineage, hashes and authority identities, safety rules,
active/next task, and authorization flags. It never contains local absolute
paths, environment values, raw HAI or label rows, attack intervals, private
numeric values, or registry content.

Layer B is local-only `.env.custody.local`. It is never committed and may hold
only `HAI_DATA_ROOT`, the MAIN registry and locator bindings, and the supplement
registry and locator bindings. Public state records only whether this layer is
configured.

## 5. Verify Git ignore before writing

Before any local binding write, require path-silent success from
`git check-ignore -q .env.custody.local`. If it is not ignored, block and do not
write private values. Do not modify `.gitignore` unless required.

## 6. Tracked safe bootstrap helper

Create `scripts/local/bootstrap_custody_bindings_v1.py`. It is public, tracked,
contains no actual path, uses only Python and the standard library, and safely
creates or updates `.env.custody.local` without echoing values.

## 7. Helper security model

The helper never prints entered or existing environment values, resolved path
objects, or exception text; suppresses expected tracebacks; never uses shell
find/locate/history, scans HOME, recursively scans the filesystem, infers HAI
location, opens test2, or scientifically parses CSV. Sensitive input uses
`getpass.getpass`.

## 8. HAI data-root definition

Without displaying a path, explain that `HAI_DATA_ROOT` is the parent whose
`hai-23.05/` child contains `hai-test1.csv` and `label-test1.csv`. No resolved
value enters a tracked file.

## 9. Interactive HAI root bootstrap

Use an existing process `HAI_DATA_ROOT` internally without printing it. If
absent, prompt once with `Enter local HAI data root (input hidden): `. Resolve
internally and require a non-symlink directory containing the edition directory
and both authorized test1 files. Do not inspect test2 or display a path.

## 10. Test1 custody check

Raw-byte hashing is allowed only for the two authorized test1 files. Expected
feature SHA-256 is
`78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be`;
expected label SHA-256 is
`eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc`.
Do not parse rows or labels or derive attack intervals. A mismatch blocks with
only `LOCAL_BINDING_BLOCKED_TEST1_HASH_MISMATCH` and saves no HAI binding.

## 11. Test2 absolute prohibition

Do not check, stat, hash, open, or inspect test2 assets or directories, and do
not derive OUTER metadata. Test2 reads remain 0.

## 12. Existing private authority bindings

For optional MAIN registry/locator and supplement registry/locator environment
bindings, check presence only. Persist exact values privately when present;
leave absent values absent. Do not print, discover, or scan for them. Locator
recovery belongs to the next authorization recovery task.

## 13. Local environment file format

Write shell-compatible `KEY=VALUE` lines with safe quoting. Require
`HAI_DATA_ROOT`; include only already-present approved optional custody keys.
Never store unrelated environment variables, API keys, provider secrets,
passwords, or tokens.

## 14. Local file permissions

On POSIX require mode 600. On non-POSIX apply the narrowest practical local
permissions. Visible output reports only `local_binding_permissions = PASS`.

## 15. Local file validation

Reload internally, require HAI root, reject unexpected keys, reconfirm test1
raw hashes, and confirm test2 was untouched. Never display file contents or
values.

## 16. Public local-binding guide

Create `docs/project_state/LOCAL_PRIVATE_BINDING_GUIDE.md` without paths. It
explains the private local layer, Git-ignore and no-chat rules, the bootstrap
command, HAI root meaning, test1 hash validation, later authorization recovery,
deletion semantics, and configured/not-configured public state.

## 17. Update START_HERE

Add a concise two-layer continuity section distinguishing public Git state and
private `.env.custody.local`. Future sessions read Git state first, check local
binding presence path-silently, never print values, and recreate the local layer
with the helper when moving machines.

## 18. Update safety boundaries

Record that the local file is private, ignored, never displayed or committed,
never recovered from history, and created interactively only by the helper with
hidden input. Test2 remains sealed.

## 19. Append decision log

Append `DEC-CONT-003`: machine custody paths live in Git-ignored
`.env.custody.local`; Git project state stores only public state and hashes.
This makes disconnected sessions resumable without public path disclosure.
Future private-custody tasks must load the local layer path-silently before any
separately authorized discovery.

## 20. Do not update authorization state

Keep `UTILITY_INNER_EXECUTION_AUTHORIZED`,
`UTILITY_INNER_D1_EXECUTION_AUTHORIZATION_ISSUED`,
`UTILITY_INNER_D1_EXECUTED`, and `REAL_UTILITY_EXECUTION_AUTHORIZED` false.

## 21. Task file

This file is the faithful repository-resident task contract.

## 22. Tracked implementation Commit A

Commit only the helper, its synthetic/static tests, local binding guide,
START_HERE and safety updates, decision-log append, and this task file. Never
include `.env.custody.local` or private output. Suggested message:
`TASK-039E3-R2R add local custody binding continuity bootstrap`.

## 23. Bootstrap helper tests

Add `tests/test_task039e3_r2r_local_custody_binding_bootstrap_v1.py` using only
temporary synthetic directories and fake files. Cover Git-ignore, unexpected
keys, missing/symlink HAI roots, missing files, wrong hashes, zero test2 opens,
value redaction, exception redaction, permissions, reload, optional binding
preservation, and exclusion of unrelated secrets. No real data.

## 24. Static verification

Run the new tests, authorization contract and independent suites,
`git diff --check`, compileall, and `pip check`. Require the authorization
regression to remain 37/37 pass, 109/109 attacks rejected, accepted invalid 0.

## 25. Commit before real local input

Commit the public path-free helper and docs before running with any real local
input. Do not alter the tracked helper in response to a private value.

## 26. Real local binding bootstrap

Run `python scripts/local/bootstrap_custody_bindings_v1.py`. Use an existing
binding internally or hidden input. If the environment cannot provide hidden
interactive input and the binding is absent, stop with
`LOCAL_BINDING_INPUT_REQUIRED`; do not search, guess, expose a path, or ask for
one in chat. Tell the user only to run the helper in a local terminal, where the
prompt is hidden.

## 27. Success output

Success output is restricted to bootstrap PASS, HAI configured, both test1 hash
matches, test2 reads 0, private paths/numeric values exposed 0, permissions
PASS, and four optional-binding presence booleans. No values are shown.

## 28. Verify no private Git entry

After success, path-safely require the local file to be ignored, untracked, and
unstaged, with no private report or tracked path. Use targeted check-ignore and
ls-files checks; do not display the file or ignored-file listings.

## 29. Update current project state

After success, update `CURRENT_STATE.md`, `CURRENT_STATE.json`,
`TASK_LEDGER.md`, and `HANDOFF.md` with boolean-only local binding presence.
Never store values.

## 30. State after pass

Set phase `UTILITY_INNER_EXECUTION_AUTHORIZATION_RECOVERY`, latest completed
task/status to this task and
`passed_task039e3_r2r_local_custody_binding_bootstrap_v1`, retain all four
authorization/execution flags false, and set exact next task
`TASK-039E3-R2R-UTILITY-INNER-EXECUTION-AUTHORIZATION-V1-PATH-SILENT-RECOVERY-R2`.

## 31. Continuity Commit B

After success, commit only the four current-state files with suggested message
`TASK-039E3-R2R record local custody binding bootstrap readiness`.

## 32. Pass status

Pass only when the helper is committed path-free and tested; the local HAI
binding exists; exact test1 hashes match; test2 reads are 0; the local file is
ignored, untracked, permission-restricted, and free of public exposure; public
state is boolean-only; and authorization remains false. Status is
`passed_task039e3_r2r_local_custody_binding_bootstrap_v1`.

## 33. Block status

If hidden input is unavailable, use status
`blocked_task039e3_r2r_local_custody_binding_bootstrap_v1_input_required` and
blocker `LOCAL_BINDING_INPUT_REQUIRED`. This is not scientific. Do not search,
guess, ask for a path in chat, or authorize. The user may run the bootstrap
helper locally and enter the value only at its hidden prompt; afterward rerun
only validation/state update in a fresh coordinator context. Any hash mismatch
also blocks without authorization.

## 34. Exact next task after pass

Do not start automatically. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-EXECUTION-AUTHORIZATION-V1-PATH-SILENT-RECOVERY-R2`.
It starts fresh, reads project state, loads the local file without printing,
performs only bounded missing-locator recovery if needed, calls the existing
preflight exactly once, issues the existing exact authorization, keeps test2
sealed and scientific execution at zero, and updates state. After that pass,
the next task is `TASK-039E3-R2R-UTILITY-INNER-D1-EXECUTION-V1`.

## 35. Final response

Return only the requested sanitized fields: status; branch/base; Bootstrap
Commit A and Continuity Commit B; push divergence and cleanliness; continuity,
helper, ignore/tracking, binding/hash/test2, optional-binding, privacy,
authorization-regression, current-state/ledger/handoff, authorization flags,
blockers, and exact-next-task fields; then STOP.
