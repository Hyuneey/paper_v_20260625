# Project continuity: start here

`docs/project_state/` is the repository-resident index and handoff layer for
recovering the current research framing, frozen authorities, task lineage,
blockers, authorization state, safety boundaries, and exact next task after a
disconnected session. It prevents chat history, external notes, terminal
history, and remembered context from becoming continuation authority.

## Mandatory read order

1. Read root `AGENTS.md`.
2. Validate and read `docs/project_state/CURRENT_STATE.json`.
3. Read `docs/project_state/HANDOFF.md`.
4. Read the active task file named by `CURRENT_STATE.json`.
5. Replay the exact canonical receipts and reports referenced by `HANDOFF.md`.

## Authority precedence

1. Explicit current user-issued task.
2. Exact committed implementation, audit, or authorization receipt.
3. Exact committed task report under `docs/task_reports/`.
4. `docs/project_state/CURRENT_STATE.json`.
5. Human-readable files in `docs/project_state/`.
6. Root `AGENTS.md` and other repository guidance.
7. Old chat, external summaries, or remembered context.

If a project-state summary conflicts with an exact committed receipt, the
receipt wins. Record the conflict and stop wherever it affects authorization
or science; never silently reconcile it.

## File lifecycle

Stable or rarely updated:

- `RESEARCH_SCOPE.md`
- `SAFETY_BOUNDARIES.md`
- `templates/*`

Append-only:

- `DECISION_LOG.md`
- `TASK_LEDGER.md`

Replaced after every completed PASS or BLOCK task:

- `CURRENT_STATE.md`
- `CURRENT_STATE.json`
- `HANDOFF.md`

Updated only when public authorities change:

- `AUTHORITY_INDEX.md`

## Resuming and closing work

To resume, follow the mandatory order, verify the self-hash and exact Git
lineage, then obey the active task's access gates. At the end of every task,
append the task ledger, replace current state and handoff, update the authority
index only when authorities changed, append the decision log only for a lasting
decision, and save the issued task specification under `TASKS/`.

This directory must never contain a private path, raw data, label details,
attack intervals, or private numeric values. Detailed evidence stays in
`docs/task_reports/`; summaries link to it instead of duplicating it.
