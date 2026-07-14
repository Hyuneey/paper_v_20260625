# Docker Partial Cleanup Protocol

TASK-028IR remediates only Docker Desktop state created by the failed
TASK-028I per-user installation. It does not alter unrelated WSL distributions,
Windows feature state, research data, credentials, or repository content.

## Ordered procedure

1. Inventory Docker processes, registration, services, shortcuts, WSL
   distributions, restart state, and the approved Docker paths.
2. Classify each path by prior existence, TASK-028I provenance, and removal
   safety.
3. Verify the installed official uninstaller signature and SHA-256.
4. Attempt the documented `uninstall` action once with a bounded timeout.
5. Re-inventory all residuals and require no prior Docker user data, no running
   Docker process, and no restart request before manual cleanup.
6. Write a deletion manifest before deleting anything.
7. Resolve and compare each target against its exact approved absolute path,
   then remove only the verified TASK-028I or official-uninstaller residual.
8. Preserve the independently verified official installer for the one clean
   retry and preserve all unrelated WSL distributions.

The cleanup never treats Docker's general residual-path documentation as
permission to delete unknown or pre-existing data.

## Boundaries

- Captured ARGOS rule access or execution is prohibited.
- KPI, SWaT, provider, and TASK-028 synthetic inputs are prohibited.
- WSL global settings, Hyper-V, Windows features, and unrelated distributions
  are unchanged.
- The cleanup does not activate any captured-rule execution approval.
