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

## DEC-D2-002

- Date: 2026-08-21
- Status: active
- Decision: D2 V1 is an INNER-development policy defined after D0/D1 INNER
  baseline characterization but frozen before any D2 execution or D2 outcome.
- Provenance: The Codex design process did not read D0/D1 prediction content
  or metric artifacts. At project level, the completed INNER baseline results
  were known and informed the D2 problem formulation before policy selection.
- Tuning boundary: No D2 fusion candidate sweep, hyperparameter search,
  execution, prediction, metric, or D2-result-based adaptation occurred. The
  distinct-source count remains the structural minimum non-singleton value of
  two, and the same-second policy remains exact.
- Confirmatory boundary: OUTER/test2 remains sealed for future confirmatory
  evaluation.
- Authority rule: The original D2 independence artifact must be interpreted
  together with provenance clarification R1.
- Canonical evidence: clarification
  `f0fbea249e11b6a3ae27a43b4b705d8537983511e2659d88f49b9c64dcf59e10`
  and receipt
  `bf049094ce211e86db22bdbdcfe78adddff76e1935cab792e594b09cf554355d`.

## DEC-D2-003

- Date: 2026-08-22
- Status: active
- Decision: The audited `PRIVATE_PARENT_PERMISSION_DENIED` failure may receive
  exactly one transparent infrastructure recovery attempt using a separate,
  outside-Git, path-redacted private custody plane.
- Historical accounting: One infrastructure-aborted attempt, zero completed
  scientific executions, and zero result-driven retries remain permanent.
- Recovery ceiling: Two total attempts, at most one completed scientific
  execution, and no third attempt.
- Scientific boundary: D2 design, original authorization, fusion, source map,
  D0/D1 predictions, temporal policy, and metrics remain unchanged.
- Canonical evidence: recovery authorization
  `0faa5c58073da28b0a3e1e9c4267aa4c16faa7723becf5d01b5ec9c391b7b141`
  and receipt
  `9b028b0132a179c12ed921207e1b20f149a10482834897f0dc9851cadde497f2`.

## DEC-D2-004

- Date: 2026-08-22
- Status: active
- Decision: The sole authorized D2 infrastructure recovery completed as total
  attempt two under the unchanged original D2 scientific semantics and the
  separate path-redacted private custody plane.
- Permanent accounting: One historical infrastructure-aborted attempt, one
  recovery attempt, two total attempts, one completed scientific execution,
  zero result-driven retries, zero remaining attempts, and no third attempt.
- Ordering: Private FusionEvidence froze before CombinedPrediction;
  CombinedPrediction froze before the single label parse and metric
  computation.
- Scientific boundary: The exact D2 design, original authorization, recovery
  authorization, D0/D1 predictions, source map, corroboration count,
  same-second policy, D0 preservation, episodes, and metric formulas were not
  changed. Result magnitude was not a gate.
- Safety boundary: D0/D1 reruns, D0 score access, rule reevaluation, test1
  feature access, test2, OUTER, current private-path exposure, tracked leakage,
  result-driven change, and push remained zero.
- Canonical evidence: CombinedPrediction
  `cf1005a03d98481b57c3ce2ad74db3e2e5d2dc3a1983d60e0aedb4f46c83b3f5`
  and receipt
  `c60d3d1707f4edb2332cfa57578a7f560c8369f2bb4f00600ac77b9896dfeb99`.
- Next authority: Independent D2 result-integrity audit only; no comparison or
  interpretation before that PASS.

## DEC-D2-005

- Date: 2026-08-22
- Status: active
- Decision: The frozen D2 recovery result passes independent result-integrity
  audit and is ready for separate INNER scientific comparison.
- Evidence: An independent stdlib audit reconstructed the exact 54,000-row
  fusion from immutable D0/D1 predictions and the source map, verified the
  private FusionEvidence and MetricEvidence hashes, reproduced all trigger and
  episode counts and all six metrics, and found zero divergences.
- Permanent accounting: Historical attempt one remains infrastructure-aborted;
  recovery attempt two remains the only completed scientific execution; result-
  driven retries and remaining attempts remain zero; no third attempt is
  authorized.
- Safety boundary: No D0/D1/D2 execution, rule reevaluation, D0 score access,
  test1 feature access, test2, OUTER, result change, new private leakage, or push
  occurred during the audit.
- Canonical evidence: readiness
  `56e49e58eea4693bf23e2a8b0fb17851f68e679015aa84fbcc874ce07161111c`
  and receipt
  `c45db852c6d5571ec7930fc12d815b383a29e31939e711eb5f2e84c69807b448`.
- Next authority: INNER D0/D1/D2 scientific comparison only; OUTER remains
  unauthorized and sealed.

## DEC-D2-006

- Date: 2026-08-22
- Status: active
- Decision: The canonical D2 V1 INNER comparison is complete. D1 detected all
  three events missed by D0, but D2 retained none of that recovery potential
  and added three normal false-alarm episodes.
- Classification: `RULE_SIGNAL_HAS_DETECTOR_MISS_RECOVERY_POTENTIAL_BUT_D2_GATE_FAILED_TO_RETAIN_IT`.
- Scientific conclusion: `CURRENT_D2_COMBINED_UTILITY_NOT_SUPPORTED_ON_INNER`.
- Boundary: This is descriptive, not causal. No alternative fusion policy was
  proposed or tested, and OUTER remains sealed.
- Disposition: `HOLD_PENDING_INNER_D2_FAILURE_DIAGNOSTIC`.
- Canonical evidence: receipt `d444ed1f7979270b945c03f2656b92e8ef7ebf8e98eca2f88f976999da00216e`.

## DEC-D2-007

- Date: 2026-08-22
- Status: active
- Decision: D2 V1 failure diagnosis is frozen as mixed mechanisms: one
  recovery event was single-source-only, two were multi-source asynchronous,
  and same-source multi-relation collapse was additionally observed.
- Normal contrast: all three D2 normal recovery false positives satisfied true
  exact-same-second multi-source corroboration; three of 574 normal D1 false-
  alarm episodes satisfied the exact gate.
- Interpretation: Complementary D1 signal and a specific structural gate
  mismatch justify a D2 V2 redesign decision, but do not authorize redesign or
  establish an optimal policy.
- Boundary: D2 V1 remains immutable; test2 and OUTER remain sealed.
- Canonical evidence: receipt `58b0a68ad4a9e4e6938e14d031ae8f6e80a7e75a071081e651ac33e5f6872f0e`.

## DEC-D2-008

- Date: 2026-08-22
- Status: active
- Decision: Freeze one D2 V2 INNER-development policy using causal active
  evidence over each COMMON-42 relation's already-public canonical selected
  horizon and requiring two distinct active source variables.
- Diagnostic provenance: D2 V1's negative result and failure diagnostic were
  known and motivated this V2. No label file was reopened, and no V2 outcome
  was observed before freeze.
- Restraint: No diagnostic gap became a parameter; no fixed global window,
  horizon multiplier, source-count search, single-source fallback, anti-FP
  simultaneous exclusion, D0 score, or rule reevaluation was introduced.
- Baseline: D2 V1 remains the immutable thesis-visible negative result.
- Confirmatory boundary: D2 V2 is not authorized or executed; test2 and OUTER
  remain sealed.
- Identifier note: `DEC-D2-005` was already occupied by the D2 V1 result-
  integrity decision, so the append-only log uses the next unique identifier.
- Canonical evidence: design
  `ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4`
  and receipt
  `df98ca12e6a83c5ae9d73c80f7a26f0b1189a3743101d5342ed908017304dd7f`.

## DEC-D2-009

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the D2 V2 result-integrity audit because two audit
  harness preflight defects were exposed only after scientific authority reads
  began, making the required exactly-once audit accounting unattainable.
- Preservation: The D2 V2 result and execution code remain byte-unchanged;
  authoritative executions, label parsing, test1-feature/test2/OUTER access,
  result-driven changes, and push remained zero.
- Evidence:
  `592344d430b50724a7ae4f81ed0e73423ec1473586d0d9a15d2ff68f6009f879`.
- Next authority:
  `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R1`.

## DEC-D2-010

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the R1 single-pass audit after its sole fresh process
  rejected the public authorization-report schema before any guarded
  scientific semantic parse.
- Root cause: The exact authorization report uses its self-hashed
  `artifact_hash` as the authorization identity and has no redundant
  `authorization_hash` field; the R1 harness incorrectly required both.
- Accounting: R1 invocations/retries/completions are `1`/`0`/`0`; all eight R1
  real scientific semantic-parse counters are `0`. Total integrity-audit
  attempts/blocked/completed are `2`/`2`/`0`.
- Preservation: The historical blocker and frozen D2 V2 result remain
  unchanged. Scientific V2 execution attempts/retries remain `1`/`0`.
  Authoritative executions, test1-feature/test2/OUTER access, result-driven
  changes, private leakage, and push remain zero.
- Evidence:
  `dc6d83a33bdf985389b6d2d1b75e54f2b703e59f515369dc41b5a499280b0990`.
- Next authority:
  `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R2`.

## DEC-D2-011

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the sole R2 audit process at public authorization
  report-provenance replay; do not retry R2.
- Root cause: The frozen Markdown body hash excludes the single separator
  newline immediately before its provenance footer. The R2 validator included
  that newline, although the frozen report itself remains exact and valid.
- Accounting: R2 invocations/retries/completions are `1`/`0`/`0`;
  authorization semantic parses are `1`; all eight real scientific semantic
  parse counters are `0`. Total integrity-audit attempts/blocked/completed are
  `3`/`3`/`0`.
- Preservation: Both historical blockers, authorization artifacts, and the
  frozen D2 V2 result remain unchanged. Authoritative executions,
  test1-feature/test2/OUTER access, result-driven changes, leakage, and push
  remain zero.
- Evidence:
  `4e6526e382dbb0bf15bae9123eeeba3a090dcb59bfd767f3b19172fe3e353c0c`.
- Next authority:
  `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R3`.

## DEC-D2-012

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the sole R3 audit at the public raw-byte Markdown
  separator gate; do not normalize the report or retry R3.
- Root cause: The committed authorization report has a CRLF immediately before
  its footer marker. R3 requires exactly one LF, rejects CRLF, and forbids
  newline normalization, so canonical extraction cannot proceed under R3.
- Accounting: R3 invocations/retries/completions are `1`/`0`/`0`;
  authorization semantic parses are `1`; all eight scientific semantic parse
  counters are `0`. Total integrity-audit attempts/blocked/completed are
  `4`/`4`/`0`.
- Preservation: All prior blockers, authorization artifacts, and the frozen D2
  V2 result remain unchanged. Authoritative executions, test1-feature/test2/
  OUTER access, result-driven changes, leakage, and push remain zero.
- Evidence:
  `2baed348b67ec7567ea57d1892c4e605728120e65480728ca562528c822e9f4a`.
- Next authority:
  `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R4`.

## DEC-D2-013

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the sole R4 audit at local private-custody binding
  replay; do not retry R4.
- Public gate: The authorization artifact identity, JSON chain, frozen
  producer semantics, canonical Markdown hash view, and footer bundle/receipt
  bindings passed without modifying frozen bytes.
- Root cause class:
  `LOCAL_PRIVATE_CUSTODY_BINDING_REPLAY_REJECTED_BEFORE_SCIENTIFIC_PARSE`.
- Accounting: R4 invocations/retries/completions are `1`/`0`/`0`;
  authorization JSON/Markdown/footer parses are `1`/`1`/`1`; all eight
  scientific semantic parse counters are `0`. Total integrity-audit
  attempts/blocked/completed are `5`/`5`/`0`.
- Preservation: All four prior blockers, authorization artifacts, and the
  frozen D2 V2 result remain unchanged. Authoritative executions,
  test1-feature/label/test2/OUTER access, result-driven changes, leakage, and
  push remain zero.
- Evidence:
  `34acc0c252b13054b15f3ac6fb1a560fdf0c653f2580305c9d582f6a52e863fc`.
- Next authority: none; explicit custody-binding remediation authorization is
  required.

## DEC-D2-014

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the sole D2 V2 private-custody binding remediation R1
  invocation during public report construction; do not retry this task.
- Forensic result: R4 failed during environment-local strict locator
  resolution under access denial, not because of a stable scientific,
  security, logical namespace, or artifact-identity mismatch.
- Private identity result: both frozen evidence hashes, logical V2 namespaces,
  outside-Git status, regular-file status, non-symlink status, tracked-copy
  count zero, and residue count zero passed path-silently.
- Root cause:
  `PRIVATE_IDENTITY_ARTIFACT_HASH_FIELD_COLLIDED_WITH_PUBLIC_REPORT_ENVELOPE_ARTIFACT_HASH`.
- Accounting: custody remediation attempts/retries/completions are `1`/`0`/`0`;
  integrity-audit attempts/completions remain `5`/`0`; scientific V2 execution
  attempts/retries remain `1`/`0`.
- Preservation: no private evidence was copied, moved, rewritten, or
  re-persisted. Scientific parses, labels, features, metrics, test2, OUTER,
  authoritative executions, private-path exposure, result changes, and push
  remained zero.
- Evidence:
  `d7b68359865cff0b8bd25ede0274fd2904729a4591d8361d17cedaf4ceb41231`.
- Next authority: none; an explicit custody-remediation report-schema task is
  required.

## DEC-D2-015

- Date: 2026-08-23
- Status: accepted
- Decision: Freeze the completed D2 V2 private-custody binding compatibility
  finding after repairing only the new report self-hash schema.
- Root cause: `artifact_hash` carried the referenced private evidence identity
  in `PrivateIdentityR1` and was also reserved for the new public report's own
  self-hash. The fail-closed collision occurred during self-hash injection
  before canonical serialization; no semantic value was overwritten or lost.
- Schema disposition: retain `artifact_hash` exclusively as the canonical
  report self-hash and map referenced authorities to role-specific
  `*_sha256` fields. Historical schemas and bytes remain unchanged.
- Custody conclusion: exact private evidence identities, custody-module
  identity, logical namespaces, stable scientific/security/logical bindings,
  and environment-local locator classification remain PASS. Absolute path
  equality is not scientific authority.
- Accounting: one report-schema remediation attempt, zero private identity
  revalidations, zero scientific/data parses or executions, 27 adversarial
  cases rejected, and zero accepted invalid.
- Evidence:
  `f7ca9d29c7e8d65359781534790c008bec436dc35e521f7de3342b7215e28cd8`.
- Next authority:
  `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R5`.

## DEC-D2-016

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the sole R5 result-integrity audit invocation at the
  frozen public execution-accounting schema gate; do not retry R5.
- Root cause: the R5 audit harness required `d1_metric_reads`, while the exact
  frozen accounting artifact uses `d1_metric_artifact_reads`.
- Oracle state before stop: all eight scientific authorities were parsed once;
  token, fusion, private FusionEvidence, CombinedPrediction, ordering,
  event/episode, six-metric, and private MetricEvidence checks passed.
- Accounting: integrity-audit attempts/blocked/completed are `6`/`6`/`0`;
  scientific V2 execution attempts/retries remain `1`/`0`.
- Preservation: zero result mutation, private evidence mutation, authoritative
  execution, feature/test2/OUTER access, result-driven change, leakage, retry,
  or push.
- Evidence:
  `0ab5479d8e2f6367e214ddeceded63826d2d89d377f2aac00d2d909d5ab322e0`.
- Next authority: none; explicit accounting-field remediation authority is
  required.

## DEC-D2-017

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the sole R5 accounting-field completion remediation
  invocation at its producer-schema parser; do not retry it.
- Root cause: the parser enumerated at most one quoted key per physical source
  line, while the frozen producer defines multiple accounting keys on some
  lines. The exact frozen schema was therefore rejected before completion
  eligibility.
- Evidence before stop: the historical R5 blocker and report matched, and the
  frozen public accounting artifact parsed once and passed its canonical
  self-hash check.
- Accounting: six historical integrity-audit attempts remain blocked; this is
  one separate completion-remediation attempt with zero retry and zero
  completion.
- Preservation: no scientific artifact, label, feature, private evidence,
  test2, or OUTER data was reopened; no scientific execution, result change,
  leakage, retry, or push occurred.
- Evidence:
  `3c5b2da933ac4e00df4602aaf89c749d6e0aea856bf844f9f769cfb907c358f2`.
- Next authority: none; an explicit accounting-schema parser remediation is
  required.

## DEC-D2-018

- Date: 2026-08-23
- Status: blocked
- Decision: Preserve the AST-only R2 implementation boundary and fail closed
  the sole real invocation without retry.
- Root cause: R2 required a historical `status` member that is absent from the
  frozen R1 blocker schema, even though the R1 blocker canonical self-hash
  matched.
- Evidence before stop: the R5 blocker/report and R1 blocker self-hash passed;
  the public accounting artifact was not parsed by the real invocation.
- Accounting: six historical full integrity audits remain blocked; completion
  remediations are now two, with zero completed evidence sets.
- Preservation: no scientific artifact, label, feature, private evidence,
  test2, or OUTER data was opened; no scientific execution, result change,
  leakage, retry, or push occurred.
- Evidence:
  `f4cacb56f9d9225874ca46cde376ea3e22df309c32047dd1805c63425ca1c982`.
- Next authority:
  `TASK-039E3-R2R-UTILITY-INNER-D2-V2-R5-EXECUTION-ACCOUNTING-SCHEMA-PARSER-REMEDIATION-R3`.

## DEC-D2-019

- Date: 2026-08-23
- Status: blocked
- Decision: Fail closed the sole R3 completion invocation without retry after
  its historical lifecycle triangulation overrequired duplicate continuity.
- Root cause: R3 required the full older R1 task ID in current continuity even
  though the exact committed task ledger already binds that task ID, blocker
  freeze commit, blocker hash, and BLOCK lifecycle state.
- Evidence before stop: R1 blocker self-hash, report, freeze paths, ledger
  binding, and continuity blocker code/hash all passed.
- Accounting: six historical full audits remain blocked; accounting completion
  remediation attempts are three and completed evidence sets remain zero.
- Preservation: the public accounting artifact was not parsed; no scientific
  artifact, label, feature, private evidence, test2, or OUTER data was opened;
  no retry, result change, leakage, or push occurred.
- Evidence:
  `863e6204325087a0560f9fbed330580931003f517b951a79ae721c6e745bff4b`.
- Next authority: none pending an explicit accounting-schema R4 remediation.

## DEC-D2-020

- Date: 2026-08-23
- Status: blocked
- Decision: Treat legacy blocker lifecycle reconstruction as non-gating
  historical provenance, while retaining exact blocker hash and freeze-ancestry
  preservation as mandatory.
- Evidence: the sole R4 invocation validated all historical identities, the
  AST-only 36-field accounting producer, all 28 accounting semantics, the R5
  full-oracle snapshot, custody compatibility, Result Freeze immutability, and
  public leakage.
- Blocker: final Markdown rendering requested `v2_recall`, but the canonical
  completion object exposes `v2_attack_event_recall`; no completion artifacts
  were written and the invocation was not retried.
- Accounting: six historical full audits remain blocked; accounting completion
  remediation attempts are four and completed evidence sets remain zero.
- Preservation: no scientific artifact, label, feature, private evidence,
  test2, or OUTER data was opened; no scientific execution, result change,
  leakage, retry, or push occurred.
- Evidence:
  `4974d124e48a74f4f4c82f71a4839c8429469047699c2a62122f222393713853`.
- Next authority: none pending an explicit report-render remediation.

## DEC-D2-021

- Date: 2026-08-23
- Status: passed
- Decision: Accept the committed R5 full scientific oracle plus the completed
  R4 public accounting audit as one D2 V2 result-integrity evidence set after
  repairing only the final typed report-render mapping.
- Root cause disposition: `RENDERER_USED_LEGACY_FIELD_NAME`; the defect was
  neither scientific, accounting-semantic, nor result-driven.
- Evidence: all `46 / 46` report fields mapped exactly, all closure and
  mutation counts were zero, `46 / 46` static tests passed, and `21 / 21`
  adversarial attacks were rejected.
- Preservation: six historical blocked full audits remain immutable; the
  scientific V2 execution remains one attempt and zero retries. No scientific
  artifact or label was reopened, no accounting semantic was recomputed, and
  test1 feature, test2, OUTER, result-driven change, leakage, and push remained
  zero.
- Completion authority:
  `b7034829527d7469459298735d253693b41f20bde6f0ab867bac71e804fa7d06`.
- Next authority:
  `TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1`.

## DEC-D2-022 — final disposition addendum to DEC-D2-006

- Date: 2026-08-23
- Status: passed
- Decision: Freeze D1 detector-complementary event information as supported,
  Rule-only operational utility as unsupported, and combined incremental INNER
  utility for both D2 V1 and D2 V2 as unsupported.
- Comparison: V1 and V2 recall are equal and both recover 0/3 D0 misses; V1
  has materially lower FAR and Pareto-dominates V2 on primary INNER utility.
- Development disposition: retain V2 as a developmental negative ablation,
  retain V1 only as the final combined confirmatory candidate, and close all
  further INNER fusion redesign and parameter search.
- Thesis boundary: remove or downgrade any combined-improvement claim; the
  complementary rule-evidence contribution and transparent negative fusion
  result remain scientifically supportable. This is not a fatal thesis blocker.
- OUTER: recommend a separately preregistered D0/D1/D2-V1 three-arm sealed
  evaluation. OUTER execution remains unauthorized.
- Receipt:
  `4f670ed37aafaeaa7324b18fdae0272d6390bd9ad0e53b5a708207e06ed5e9cc`.
- Exact next task:
  `TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-PREREGISTRATION-AND-AUTHORIZATION-V1`.

## DEC-OUTER-001 authorization addendum

- Date: 2026-08-23
- Status: passed
- Decision: Freeze and authorize one sealed HAI-23.05 test2 confirmatory
  execution of exactly D0 detector-only, D1 COMMON-42 Rule-only, and D2 V1
  exact-same-second two-source detector-preserving fusion.
- Authority boundary: the execution must use one shared immutable feature
  snapshot, freeze and durably validate all three predictions before label
  access, and apply only the preregistered event, episode, primary, and
  descriptive secondary metrics.
- One-shot boundary: one coordinated scientific attempt, zero retries, no D2
  V2, no recalibration, no fusion change, no parameter search, and no
  post-OUTER redesign.
- Seal preservation: this authorization task used frozen manifest metadata
  only; real test2 feature and label accesses, parses, scientific executions,
  and OUTER executions all remained zero.
- Preregistration / authorization:
  `66179921042faecf189fe93ddaf20bb06669afa6e27dbefb67c9b95eabb93427` /
  `fb8abb3a342c591873d15d4bcf28cbdcc7363fce77a228f486f122ef5933ac14`.
- Receipt:
  `1ef346ec824561def8d09c8c09211c11fa2eb5c2bb415c95d2008b4af6a03d4d`.
- Exact next task:
  `TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-EXECUTION-V1`.

## DEC-OUTER-002 — pre-real custody and redaction blocker

- Date: 2026-08-23
- Status: blocked before scientific attempt.
- Decision: fail closed before test2 access because the current local custody
  configuration lacks complete frozen D0 private bindings and the diagnostic
  path-redaction boundary was violated.
- Scientific preservation: OUTER attempts/retries remain `0 / 0`; test2
  feature and label accesses/parses, all arm executions, prediction freezes,
  and metric computations remain `0`.
- Authorization disposition: the frozen one-shot authorization is unchanged;
  it was not consumed and no result was observed.
- Blocker:
  `5277ae39a2558344499abfca92906107f77b4416c457599c314f69f8e4c75d72`.
- Exact next task:
  `TASK-039E3-R2R-UTILITY-OUTER-PRE-EXECUTION-PRIVATE-CUSTODY-AND-PATH-REDACTION-REMEDIATION-V1`.

## DEC-OUTER-003 — custody remediation V1 binding-schema blocker

- Date: 2026-08-23
- Status: blocked before private locator resolution.
- Decision: preserve the single V1 infrastructure invocation as failed and do
  not retry it. The remediation allowlist used legacy D1 binding-key names and
  rejected the current canonical local authority-key schema.
- Additional custody finding: the currently bound HAI custody root contains no
  frozen D0 private-artifact directory; exact D0 locators must be recovered
  from their approved environment-local custody source.
- Scientific preservation: OUTER attempts consumed/remaining remain `0 / 1`;
  test2 access, model/threshold validation, sentinel execution, inference,
  Rule evaluation, fusion, metrics, result change, and new leakage remain `0`.
- Blocker:
  `ab428d3167608dda96225c9d9b7c89b4c65760cc2cc99fc054aa317d2126c65c`.
- Exact next task:
  `TASK-039E3-R2R-UTILITY-OUTER-PRE-EXECUTION-PRIVATE-CUSTODY-AND-PATH-REDACTION-REMEDIATION-R2`.
