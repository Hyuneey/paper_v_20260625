# HAI 23.05 Official Distribution Remediation

The pinned `icsdataset/hai` Git snapshot and its ten Git-LFS pointers remain
the dataset identity and integrity authority. TASK-039AR authorizes the
official Kaggle dataset `icsdataset/hai-security-dataset` only as a selective
payload transport after the original repository exhausted its LFS budget.

Metadata is frozen before payload access. The public receipt records owner,
slug, exact dataset version, timestamp, license, complete file inventory,
advertised sizes, API/client version, and an artifact hash. It deliberately
omits credentials, authorization material, response URLs, and signed download
URLs.

Each allowlisted file is requested separately. A per-file archive must contain
exactly one matching member. Its extracted SHA-256 and byte size must equal the
Kaggle advertised size, pinned Git-LFS OID and pointer size, and TASK-039A
expected hash and size. No whole-dataset endpoint, HAIEnd payload, or earlier
HAI payload is permitted.

A byte-equivalence pass grants provenance materialization only. It grants no
scientific data access, process choice, variable typing, candidate generation,
model training, detector execution, split creation, or evaluation authority.
