# RCC Source Authority Decision

- Date: `2026-08-29`
- Status: `APPROVED`
- Source: user-approved RCC-001 source policy
- Related decisions: `DECISION-001`, `DECISION-002`

## Decision

Use `origin/research-v6-thesis-checkpoint` at
`2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` as the scientific source of truth,
with `thesis-v1-post-push-audit` as the immutable pin at the same commit.

Index
`origin/task-039e3-r2r-thesis-draft-scaffold-v1@ebc5a57bfdb7d8266f96f2990338effb9d0a2743`
only as a read-only documentation overlay.

## Consequence

Scientific implementation and result claims derive from the pinned checkpoint.
The overlay may supply narrative context but cannot override scientific
authority. A current checkout is not authoritative merely because it is
checked out.
