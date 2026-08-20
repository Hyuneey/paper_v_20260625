# TASK-039E3-R2R-UTILITY-INNER-D1-RESULT-INTEGRITY-AUDIT-V1

## Purpose

Independently certify whether the exact frozen first real INNER D1 Rule-only
result is internally consistent with its authorized execution protocol. This
task audits provenance, immutable bytes, bridge identity, full-census closure,
label blindness, alarm episodes, label/attack-event custody, metric arithmetic,
single-attempt accounting, test2 exclusion, and public leakage. It does not
judge scientific quality.

## Exact lineage and identities

- Base: `f53e1c41d3e91a36a74e5cb078cce850dd499aa0`.
- Execution Bridge Commit A: `936296cdcf9f5d87658a0c9993856ccc7d9222b2`.
- Independent Audit Commit B: `c880042d1a49c12e2a6788d618bfb9b5491e1be0`.
- Result Freeze Commit C: `9fe9192c6da4e2d1f3c7a42ecdd28006e8534449`.
- Authorization: `deb08014de20c398d2dcde046e14b505a65af2d52cb6eb309fc8188f020b5834`.
- Committed grant: `642bcaedd513dab9c1e98f70633a276e86969819a2f2d6e52897f9c36f3bf856`.
- Bridge identity: `959de0f2ed781f404f583af75f7938bda56634024ddfbf23ecc9c38f5704edfe`.
- RulePrediction: `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`.
- Private metric evidence: `2d865315d1c329ffb3e87ebed6a538dee82be123c32b7ee9ffe245c7eb234d2b`.

## Immutable boundaries

No production, frozen authorization, bridge, result, metric, COMMON-42,
numeric-authority, R3, or V4 file may change. The audit may add only this task
specification, its audit script, and two new synthetic/static test modules,
followed by sanitized audit reports and a separate project-state update.

The audit must never call the real D1 execution entry point or rule loop. D0,
D2, detector, OUTER, test2, recalibration, and scientific tuning are prohibited.

## Public audit

Replay the exact commit boundaries and compare all eight current result files
byte-for-byte with Result Freeze Commit C. Validate seven JSON self-hashes,
their closed schemas and cross-bindings, and the Markdown report through exact
Git-blob custody. The RulePrediction schema intentionally has no `task_id`
field; its task identity is validated through its closed artifact type,
authorization, bridge commit, execution mode, and exact pinned artifact hash.
This classification does not alter frozen bytes.

Recompute all 6,031 public trace identities, state/alarm invariants, ten MAIN
reference identities per prediction, unique opportunity closure, and the
label-blind alarm episode oracle. Re-run only static/synthetic bridge tests:
32 or more semantic cases, zero divergence, at least 40 attacks, zero accepted
invalid.

## Coordinator-only private audit

Read MAIN once, supplement once, test1 once, and label-test1 once. Validate
their exact canonical hashes. Independently parse the frozen 22-feature test1
frame, use frozen lower-level V3/V4 authorities to derive source events and the
ordered opportunity census, and compare that census to the committed
RulePrediction artifact. Do not evaluate any rule outcome.

Freeze the alarm oracle before label access. Then derive maximal contiguous
strict-one attack events, recompute Attack-event recall and normal FAR
episodes/hour, and reproduce the private metric-evidence hash. Public output
contains only booleans, approved hashes, and aggregate counts—not label rows,
interval coordinates, hidden denominators, raw values, private numeric values,
or paths.

## Expected closure

- Raw/retained/isolated/opportunity counts: `27256 / 5490 / 3023 / 6031`.
- Evaluated/alarm/episode/abstain/error: `6031 / 788 / 626 / 0 / 0`.
- Execution attempts/retries: `1 / 0`.
- Audit census replays/rule executions/metric recomputations: `1 / 0 / 2`.
- Test2 accesses: `0`.
- Accepted invalid: `0`.

On PASS, set result-integrity audited and interpretation-ready true while D0,
D2, detector, and OUTER remain unauthorized. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-BASELINE-DESIGN-AND-FREEZE-V1`.
