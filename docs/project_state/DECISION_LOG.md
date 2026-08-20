# Decision log

Append new entries; never rewrite historical decisions.

## DEC-CONT-001

- Date: 2026-08-20
- Status: active
- Decision: Repository state, not chat memory, is the continuation authority.
- Rationale: Future sessions require deterministic, reviewable recovery.
- Consequence: Sessions replay Git state and receipts before acting.
- Supersedes / Superseded by: none / none.
- Canonical evidence: this continuity bootstrap task and `START_HERE.md`.

## DEC-CONT-002

- Date: 2026-08-20
- Status: active
- Decision: `docs/task_reports/` remains canonical detailed evidence;
  `docs/project_state/` is only an index and handoff layer.
- Rationale: Mutable summaries must not displace immutable detailed receipts.
- Consequence: Conflicts resolve in favor of exact committed receipts.
- Supersedes / Superseded by: none / none.
- Canonical evidence: `START_HERE.md` authority precedence.

## DEC-UTILITY-001

- Date: 2026-08-20
- Status: active
- Decision: COMMON-42 is the canonical utility portfolio; historical T2
  membership is excluded.
- Rationale: The frozen V4 R1 and evaluator authorities bind exactly 42 COMMON
  relations with T2 false.
- Consequence: Utility authorization must reject T2 or alternate portfolios.
- Supersedes / Superseded by: historical T2 utility membership / none.
- Canonical evidence: `AUTHORITY_INDEX.md` and R3 independent receipt.

## DEC-UTILITY-002

- Date: 2026-08-20
- Status: active
- Decision: MAIN 420 references are relation-execution authority; supplement
  6 references are source-census isolation only. They are not one
  interchangeable 426-record authority.
- Rationale: Their roles and custody contracts are distinct.
- Consequence: Execution and isolation validation must preserve both types.
- Supersedes / Superseded by: none / none.
- Canonical evidence: source-census final receipt and combined contract.

## DEC-UTILITY-003

- Date: 2026-08-20
- Status: active
- Decision: D1 Rule-only executes before detector and D2 work.
- Rationale: D1 establishes the first bounded utility result independently.
- Consequence: D0, D2, detector, and fusion remain unauthorized.
- Supersedes / Superseded by: none / none.
- Canonical evidence: active authorization recovery task.

## DEC-UTILITY-004

- Date: 2026-08-20
- Status: active
- Decision: D1 and future D2 must consume the same frozen RulePrediction
  content.
- Rationale: Comparison must not change rule predictions between arms.
- Consequence: Future D2 binds the immutable D1 prediction artifact.
- Supersedes / Superseded by: none / none.
- Canonical evidence: R3 comparison boundary receipt.

## DEC-UTILITY-005

- Date: 2026-08-20
- Status: active
- Decision: Authorization and scientific execution are separate tasks.
- Rationale: Custody and scope must freeze before any label-aware computation.
- Consequence: This task cannot execute D1 even after issuing its grant.
- Supersedes / Superseded by: none / none.
- Canonical evidence: authorization contract and active recovery task.

## DEC-PRIVACY-001

- Date: 2026-08-20
- Status: active
- Decision: Any private path disclosure is a terminal task blocker even without
  file access.
- Rationale: Custody identity itself is sensitive.
- Consequence: Stop, issue no authorization, and retain only a sanitized blocker.
- Supersedes / Superseded by: none / none.
- Canonical evidence: historical authorization blocker artifact.

## DEC-PRIVACY-002

- Date: 2026-08-20
- Status: active
- Decision: Private custody recovery occurs in a fresh, single-coordinator,
  path-silent process.
- Rationale: Path-bearing history is contamination, not authority.
- Consequence: No log recovery, broad search, or path-bearing command output.
- Supersedes / Superseded by: none / none.
- Canonical evidence: active recovery task.

## DEC-OUTER-001

- Date: 2026-08-20
- Status: active
- Decision: Test2 remains sealed until separate OUTER authorization.
- Rationale: INNER results must not influence sealed evaluation.
- Consequence: Test2 access, hashing, parsing, and attack inspection remain zero.
- Supersedes / Superseded by: none / none.
- Canonical evidence: V4 R1 and active recovery task.

## DEC-CONT-003

- Date: 2026-08-20
- Status: active
- Decision: Machine-specific custody paths are maintained in a Git-ignored
  `.env.custody.local` private continuity layer, while Git-tracked
  `docs/project_state/` stores only public state and hashes.
- Rationale: Chat and Codex sessions can disconnect; machine paths cannot
  safely live in Git or chat; environment-only bindings disappear across
  sessions; a local-only persisted binding file provides resumability without
  public disclosure.
- Consequence: Future private-custody tasks load bindings path-silently from
  the local layer before attempting any separately authorized discovery.
- Supersedes / Superseded by: none / none.
- Canonical evidence: local custody binding bootstrap helper and
  `LOCAL_PRIVATE_BINDING_GUIDE.md`.

## DEC-DATA-001

- Date: 2026-08-20
- Status: active
- Decision: The HAI INNER payload may be reproducibly reconstructed in a fresh
  execution environment from the exact pinned official acquisition authority.
  Local cache paths are disposable machine state; the official source commit
  and exact payload hashes are scientific and custody authority.
- Rationale: Reproducible official materialization removes machine-path
  dependence without weakening provenance or asking users to disclose a local
  path.
- Consequence: Authorization recovery may create a private cache containing
  only the authorized test1 feature and label payload, bind it locally, and
  keep test2 sealed. Moving refs, mirrors, unverified archives, and cache paths
  remain unauthorized.
- Supersedes / Superseded by: the assumption that HAI must preexist on the
  current execution machine / none.
- Canonical evidence: TASK-039A source receipt, TASK-039AR byte-equivalence
  receipt, and the code-materialized HAI recovery task.

## DEC-CUSTODY-001

- Date: 2026-08-20
- Status: active
- Decision: For rematerializable private numeric authorities, the frozen
  private-registry content hash is the portable scientific authority. A local
  locator is a machine-specific custody pointer whose self-hash is not
  required to remain identical across machines.
- Rationale: Registry content is deterministically derived from frozen normal
  data, while locator bytes include disposable machine state. Conflating those
  identities prevents exact cross-machine recovery without strengthening
  scientific custody.
- Consequence: Every fresh locator must remain local-only, canonical,
  self-hashed, outside Git, regular and non-symlinked, point to the exact
  validated registry, bind its frozen content hash, and bind the correct
  materialization authority. Alternate numeric values remain prohibited.
- Supersedes / Superseded by: historical locator self-hash as a current-machine
  acceptance condition / none.
- Canonical evidence: Portable Contract Commit A
  `1d7b47daf053ffbcbf69499b55b68ce7c2838e83` and Portable Independent Audit
  Commit B `da3872530f45fb0093d815c9f50fe08216cc2fda`.
