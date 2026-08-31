# VALIDATION V2

VALIDATION V2 is a prospective scientific version. It does not rewrite,
migrate, or relabel PILOT V1.

Start with these controls:

1. `VERSION_POLICY.md` defines the V1/V2 boundary.
2. `DECISION_GATES.md` defines the only user decision gates.
3. `TASK_INDEX.csv` is the ordered implementation ledger.
4. `PROGRAM_STATE.json` is the machine-readable program status.
5. `PILOT_V1_PRESERVATION_MANIFEST.json` binds the immutable authority.

The current development split is `test1`. It remains development-only.
No test2 or other held-out access is authorized by this program.

## Current execution status

- Shared V2 authority, custody, protocol, metric, and experiment-preparation
  contracts are frozen and synthetic-tested.
- The clean-checkout fresh-machine synthetic rehearsal passed without
  scientific data.
- Stage 3 scientific execution is fail-closed because the authorized
  normal-only HAI custody binding is not present in this environment.
- Do not search for restricted data or reuse PILOT V1 private inputs. Restore
  an explicit VALIDATION V2 custody binding before executing EXP-01 or EXP-02.
- EXP-03 remains additionally gated by DG-03 immediately before any provider
  contact.

## Resume receipt

- `DEC-020 = APPROVED_FORMAL_V4`
- `DG-01 = RESOLVED_BY_USER`
- Canonical-to-V4 bridge: `NOT_SELECTED`
- Minimum thesis path bridge requirement: `NOT_REQUIRED`
- Normal custody recovery: `BLOCKED_NORMAL_DATA_NOT_FOUND`
- Approved locator configured: `false`
- Scientific payload opens, hashes, parses, and label accesses in the recovery
  stage: `0`

The blocker means no approved locator was configured. It does not claim that
the files are absent somewhere on the host. Configure an explicit authorized
`HAI_NORMAL_ROOT` or ignored local custody binding to the parent of
`hai-23.05/`; never perform a host-wide search.
