# Research Control Center

## What this is

The Research Control Center (RCC) is the human-readable operating layer for
this thesis project. It separates what exists in code from what has been run,
audited, reproduced, and supported strongly enough for a research claim.

RCC version: `0.1.0`
Scientific authority: `origin/research-v6-thesis-checkpoint` at
`2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Read in this order

1. [CURRENT_CONTEXT.md](CURRENT_CONTEXT.md)
2. [MY_TODO.md](MY_TODO.md)
3. [dashboard/index.html](dashboard/index.html)
4. [history/PROJECT_TIMELINE.md](history/PROJECT_TIMELINE.md)
5. [architecture/](architecture/README.md)
6. [registry/](registry/README.md)

## Scientific source authority

Scientific implementation and result claims come from the exact checkpoint
above. The immutable tag `thesis-v1-post-push-audit` points to the same commit.
The thesis draft at
`origin/task-039e3-r2r-thesis-draft-scaffold-v1@ebc5a57bfdb7d8266f96f2990338effb9d0a2743`
is a read-only narrative overlay, not scientific authority. See
[SOURCE_AUTHORITY.md](SOURCE_AUTHORITY.md).

## Current research phase

**EVALUATION_SCOPE_EXPANSION**

Architecture implementation and frozen INNER pilot operation are complete.
Scientific validation is partial; expanded evaluation and hypothesis
validation remain incomplete. This is not a claim of final thesis validation.

Current operational stop: `DG05-PRODUCTION-CHAIN-CLOSURE-001` is
`DECISION_REQUIRED / NO_GO_FOR_REAL_DG05_ACCESS`. The preserved audit and
prospective closure components do not constitute an executable release or an
approval. Exact next is DEC-031, the consolidated scenario/time/runtime and
normal-source binding decision. No primary held-out result exists.

## Important distinction

`Implemented` and `Executed` are engineering states. `Evidence-reviewed` means
the component's source or evidence status was reviewed against the pinned
authority; it is not performance validation. `Result-integrity audited` is a
separate result-specific check of custody, immutability, ordering, and
arithmetic. `Independently reproduced` requires a separate reproduction under
the required environment and custody. Scientific claim status comes only from
`registry/claims.csv`.

The compatibility field `component.claim_ready` supports narrow implementation
or contract wording only. It does not mean scientifically validated performance.

These counts are not a single completion percentage. Code existence, execution,
evidence review, result-integrity audit, independent reproduction, and
scientific validation are separate states.

## How to update RCC

1. Update the registry first and keep every scientific row bound to the pinned
   authority.
2. Run `research_control_center/scripts/refresh_all.py`.
3. Review the generated summaries and dashboard for unsupported wording.
4. Record material decisions and checkpoints under `history/`.
5. Commit only RCC changes after validation; never edit generated views by
   hand when their source is registry data.

History is curated rather than exhaustive. User-context-only events must keep
their approximate precision and confidence, and they may not override current
state or `claims.csv`.
