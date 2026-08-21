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

## DEC-CUSTODY-002

- Date: 2026-08-20
- Status: active
- Decision: A runtime registry validator whose canonical authority builder
  requires frozen public construction documents must receive those exact
  documents explicitly. Missing builder arguments are an orchestration defect,
  not evidence that an exact registry is invalid.
- Rationale: The canonical MAIN registry artifact and self-hash were exact and
  the unchanged validator accepted it when supplied the frozen executable-
  equivalence and construction-evidence inputs.
- Consequence: Portable preflight control revision `R2_PORTABLE_PREFLIGHT`
  replays those two public inputs before registry validation. It does not add
  defaults, weaken registry validation, or alter any numeric authority.
- Supersedes / Superseded by: zero-argument MAIN authority builder invocation
  in portable preflight / none.
- Canonical evidence: Diagnostic/Remediation Commit A
  `157bc470ba1850093a02b5baee3e5eb446071aea`, Independent Audit Commit B
  `bbbcf2fff841a33253b6732dd0cdc6af344d6a6f`, and root-cause artifact
  `653a0da64db57c88d54a318b3fc7df54cb1f201ae9baea67b55f964bb16b3a73`.

## DEC-D0-001

- Date: 2026-08-20
- Status: active
- Decision: The primary D0 reference detector is frozen as
  `D0_PCA_SPE_V1` before any detector training, test evaluation, or D2 design.
- Rationale: PCA-SPE is a standard, deterministic, normal-only multivariate
  process-monitoring baseline that is reproducible, tractable, label-free in
  fit/calibration, and scientifically distinct from the graph-guided rule
  mechanism. Detector novelty is not the research contribution.
- Consequence: Future D0 work must consume design hash
  `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`
  without changing the feature scope, normal split roles, PCA target, score,
  threshold, episode, or metric policies. D1 performance may not tune D0.
- Supersedes / Superseded by: none / none.
- Canonical evidence: Design Commit A
  `4bdb16701a84b383f713629524a20900bba27d95`, Independent Audit Commit B
  `4e4e904cca8779e5dde62bcea697e6d40d58a867`, and Design Freeze Commit C
  `2528632fca2c64e1bd4a293d57bed56cc3e5665b`.

## DEC-D2-001

- Date: 2026-08-21
- Status: active
- Decision: The primary D2 arm is frozen as detector-preserving,
  exact-same-second multi-source verified-rule corroboration. A recovery alarm
  requires at least two distinct canonical COMMON-42 source variables.
- Rationale: Two is the minimum non-singleton distinct-source corroboration
  count. It separates a single initiating source from cross-variable physical
  corroboration without adding a learned threshold, temporal window, score
  gate, or label-dependent choice.
- Consequence: Every frozen D0 alarm is preserved. D1 contributes only positive
  detector-miss recovery, using exact frozen D1 alarm records and their
  relation bindings. D0 score access, D0 suppression, rule rerun, any-rule OR,
  AND, weighting, temporal tolerance, and later INNER tuning are prohibited.
- Independence: Frozen before D2 execution and without D0/D1 prediction
  content, metric-artifact, test1, label, private, test2, or OUTER access.
- Supersedes / Superseded by: none / none.
- Canonical evidence: Design Commit A
  `8bb227521f28101970e7ea19ae97987d94b3c7c3`, Independent Audit Commit B
  `03e58a79842d6f6aa0675595e6f78fca86b76de6`, Design Freeze Commit C
  `5ad1c2fb56432be637c177cf64449238fdc1b504`, and design hash
  `eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51`.
