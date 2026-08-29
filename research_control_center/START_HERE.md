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
4. [architecture/](architecture/README.md)
5. [registry/](registry/README.md)

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

## Important distinction

`Implemented` means code exists. `Executed` means an authorized run exists.
`Audited` means that execution or artifact passed its defined checks.
`Reproduced` means it was independently recreated under the required custody.
`Claim-ready` means the evidence supports the permitted research wording.

These states are not interchangeable:

`CODE EXISTS != EXECUTED`
`EXECUTED != VALIDATED`
`VALIDATED != GENERALIZED`
`GENERALIZED != CLAIM_READY`

## How to update RCC

1. Update the registry first and keep every scientific row bound to the pinned
   authority.
2. Run `research_control_center/scripts/refresh_all.py`.
3. Review the generated summaries and dashboard for unsupported wording.
4. Record material decisions and checkpoints under `history/`.
5. Commit only RCC changes after validation; never edit generated views by
   hand when their source is registry data.
