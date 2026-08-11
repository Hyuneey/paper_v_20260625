# Construction-Evidence Materialization

TASK-039E1 converts the audited 42-relation identity cohort into two bound
views:

- a private, self-hashed evidence ledger containing deterministic calibrated
  values and their full D0/D1/D2 provenance;
- a public reference-only manifest and cohort containing hashes, roles, and
  relation identities without the private calibrated values.

Each relation contains exactly eleven numeric roles: three D1-derived
parameter roles, one D1-selected horizon, and seven preregistered D0 window
constants. Numeric references bind the relation identity, value, origin,
source/target parameter records, D1 fit evidence, D2 confirmation evidence,
and shared window bundle.

Resolving a numeric reference is construction-only. It does not grant runtime
authority and cannot produce a Rule v2. No HAI file or model/provider path is
part of the materialization implementation.
