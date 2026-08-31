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
