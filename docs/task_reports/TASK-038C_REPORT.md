# TASK-038C Report

Status: `passed_review_agent_inner_branch_experiment`

TASK-038C executed the leakage-corrected, inner-only ReviewAgent component
experiment over the frozen A2 and A3 branch-parent population. Initial and
repaired parent rules were executed or hash-verified on full inner values, and
all parent predictions were frozen before inner-label access. A Review call was
authorized only when the direction-specific detector–rule composition had
lower direct PA-free inner point F1 than the matching detector-only baseline.
Each triggered A2 or A3 branch received at most one independent Review
revision, with no retry, replacement, or Repair call. Reviewed rules were
extracted, statically audited, executed on generation target and contrast
values, and replayed deterministically on full inner values before post-review
metrics were computed. Invalid and harmful revisions were not reverted.
TASK-038C reports Review trigger frequency, executable-revision yield, paired
inner effects, A2/A3 generation variability, and post-Repair Review effects.
It does not access outer or sealed-test data and does not establish outer
generalization or full ARGOS methodological validity.

## Population and Trigger Freeze

| Measure | Result |
|---|---:|
| A2 total records | 96 |
| A2 executable parents | 83 |
| A2 non-applicable records | 13 |
| A3 executable parents | 96 |
| Executable logical Review parents | 179 |
| Unique executable parent rules | 96 |
| Parent predictions reused from TASK-037E | 83 |
| Repaired parents replayed twice | 13 |
| Review required | 77 |
| No Review needed | 102 |
| A2 Review calls | 36 |
| A3 Review calls | 41 |

All parent predictions were frozen before labels were loaded. Review calls were
authorized only by the frozen direct PA-free point-F1 comparison. The exact
77-slot manifest was committed before provider access.

## Operational Result

| Measure | A2 | A3 |
|---|---:|---:|
| Executable parents | 83 | 96 |
| Review required | 36 | 41 |
| Trigger rate | 0.4337 | 0.4271 |
| Responses captured | 36 | 41 |
| Rules extracted | 36 | 41 |
| Static-valid revisions | 36 | 41 |
| Reviewed executables | 35 | 41 |
| Reviewed executable rate | 0.9722 | 1.0000 |

One A2 FN revision failed the generation-target runtime contract and remained a
terminal invalid outcome. No parent fallback, repair, retry or replacement was
used.

## Inner-Only Effects

Invalid or non-executable revisions remain in the attempted-call denominator.
Numeric deltas are conditional descriptive summaries among executable
revisions.

| Measure | A2 | A3 |
|---|---:|---:|
| Improved inner point F1 | 34 | 38 |
| Equal inner point F1 | 1 | 0 |
| Regressed inner point F1 | 0 | 3 |
| Invalid or non-executable | 1 | 0 |
| Improvement success rate | 0.9444 | 0.9268 |
| Non-regression success rate | 0.9722 | 0.9268 |
| Detector baseline reached rate | 0.5000 | 0.4878 |
| Harmful or invalid rate | 0.0278 | 0.0732 |
| Conditional mean point-F1 delta | 0.1871 | 0.1749 |
| Conditional median point-F1 delta | 0.1634 | 0.1659 |

Both branches satisfy the predeclared
`substantial_inner_review_signal` description. This label applies only to
inner behavior and does not establish outer generalization.

Directionally, A2 had 8 FN calls and 28 FP calls; 7 FN and 27 FP revisions
improved, one FP revision was equal, and one FN revision was invalid. A3 had 9
FN calls and 32 FP calls; 8 FN and 30 FP revisions improved, while one FN and
two FP revisions regressed. FN recovery costs and FP true-positive removals
remain present in the per-branch effect records even when point F1 improved.

## Post-Repair Review

The thirteen repaired parents produced five Review triggers and eight
`no_review_needed` identities. All five reviewed outputs were executable; four
improved inner point F1 and one regressed. This is an incremental Review
description after Repair, not a balanced factorial interaction.

## Independent A2/A3 Review Variability

For the 36 initially executable slots where both branches required Review,
A2 and A3 shared the same parent and prompt payload but used distinct branch
requests and provider calls.

- Identical response rate: 0.0000
- Identical reviewed-rule rate: 0.0000
- Median absolute post-review point-F1 difference: 0.0198
- A2 better: 17
- A3 better: 11
- Ties among comparable executable pairs: 7

These differences measure stochastic Review generation variability. They are
not a RepairAgent effect.

## Provider Usage

| Usage | A2 | A3 | Total |
|---|---:|---:|---:|
| Calls | 36 | 41 | 77 |
| Input tokens | 86,555 | 100,177 | 186,732 |
| Cached input tokens | 0 | 83,875 | 83,875 |
| Output tokens | 59,237 | 72,016 | 131,253 |
| Reasoning tokens | 34,654 | 42,583 | 77,237 |
| Total tokens | 145,792 | 172,193 | 317,985 |

Provider errors, transport errors, retries, replacement calls, RepairAgent
calls and DetectionAgent calls were all zero. Cost is
`not_computed_unfrozen_pricing`.

## Commit Boundary Note

Provider calls were executed from the clean, then-current Commit B
`91ae6ec81a455bcbef826057ee7b974724b6d9d0`. Before any reviewed-rule
container execution, a runtime-only parent-registry lookup defect was found.
No provider call was repeated. The unpushed local history was autosquashed so
the correction remains in implementation Commit A
`d627283e11e4f43f8273dafaa7a4dd0430d47c29`, and the content-equivalent
freeze is Commit B `c468db02efd8478eaa407323410f3e6149f85eea`.

## Safety and Claim Boundary

Generated code never executed on the host. The frozen rootless Podman boundary
used no network, non-root execution, a read-only root, dropped capabilities,
no new privileges, and bounded CPU, memory, PIDs and timeout. Containers
received values only; labels and detector predictions were not mounted.

No outer value, outer label, sealed-test artifact, branch selection, detector
retraining, threshold reselection or Full Aggregator evaluation was accessed
or performed. Raw rules, prompts, responses, values, labels, predictions,
regression windows, receipts and private paths remain ignored and untracked.
Structural and prediction drift are descriptive and do not establish semantic
equivalence.
