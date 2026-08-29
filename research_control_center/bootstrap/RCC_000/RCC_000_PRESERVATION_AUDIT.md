# RCC-000 Preservation Audit

## Current remote preservation

Live read-only remote verification confirmed:

| Item | Commit / object | Status |
|---|---|---|
| `research-v6-thesis-checkpoint` | `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | PASS |
| `thesis-v1-post-push-audit` | annotated tag peeling locally to `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | PASS |
| `thesis-v1-first-results` | annotated tag peeling locally to `5aa7c61ee37fb232c9b487e448ddbd30e3628872` | PASS |
| thesis draft remote branch | `ebc5a57bfdb7d8266f96f2990338effb9d0a2743` | PASS |

The canonical remote checkpoint therefore preserves the full public source,
frozen INNER results, OUTER blocker metadata, professor package, and post-push
audit. The thesis draft is separately preserved as a documentation-only child.

## Local preservation assets

| Logical asset | SHA-256 | Bytes | Validation | Currency |
|---|---|---:|---|---|
| `repository-all-refs.bundle` | `232b6c9c0224e1109878e571ed0f45c2703e38e6e2e20426afe55cd5cd591dd1` | `18,889,326` | `git bundle verify` PASS; complete for captured history | stale for later checkpoint/thesis refs |
| `source-only-head.zip` | `8427aacf47697b045224349ccd898d722a9360dfe99660ffb15a4c87ee7b0b3d` | `2,949,430` | hash matches public manifest | pre-checkpoint source snapshot |

The bundle's recorded heads include the OUTER continuity at `70811efe...`, but
not the later `5aa7c61e...`, `2dc7e6c2...`, or `ebc5a57b...` heads. It remains a
valid historical backup, not the latest canonical backup.

## Tracked preservation metadata

- Environment manifest: present and sanitized.
- Canonical local branch/commit inventory: present.
- Thesis artifact index: present.
- Root `CURRENT_PROJECT_STATE.md`: present on the checkpoint, but its basis is
  older than the checkpoint and must not override later exact refs/artifacts.
- Professor submission package: present on the canonical checkpoint.
- Post-push checkpoint audit: present and tagged.
- Thesis scaffold: present only on the separate thesis branch.

## Worktree condition

Git reports `143` registered worktrees, including `21` detached worktrees. This
is historical operational state, not scientific authority. RCC should resolve
evidence by ref/commit/path and should not infer authority from an existing
worktree directory. Cleanup was not attempted.

## Recommendation

After the user approves the RCC canonical-source/overlay policy, create a new
local all-refs bundle or an exact canonical+thesis preservation set. Do not
overwrite the existing historical bundle. This recommendation is not a
precondition for reading the already verified remote checkpoint in RCC-001.

`PRESERVATION_AUDIT = PASS_WITH_STALE_LOCAL_BACKUP_CONDITION`
