# TASK-039E3 R2R Normal-Only Authority V1 Materialization

Status: `passed_task039e3_r2r_utility_normal_only_authority_v1_materialization`

## Selective reacquisition

The frozen TASK-039AR version-10 Kaggle route selectively reacquired exactly two files: `hai-23.05/hai-train1.csv` and `hai-23.05/hai-train2.csv`. Each matched the TASK-039A SHA-256 and byte size, historical Git-LFS pointer identity, and frozen Kaggle advertised size. No whole-dataset endpoint, HAIEnd payload, earlier HAI version, train3, test, or label file was requested.

An ephemeral runner initially failed while importing the hashing helper, before any network request or file creation. The corrected runner reused the historical helper from its frozen module. Two network file requests then completed successfully.

## Canonical materialization

The committed authorization and control/dependency source identities were revalidated before scientific parsing. The canonical materializer derived 9 unique sources, 10 unique targets, and a 19-feature union from the frozen COMMON relations.

- Canonical invocations: 1
- Scientific retries: 0
- Train1 scientific parses: 1
- Train2 scientific parses: 1
- Relations: 42
- Roles: 10
- Records: 420
- Unique logical keys: 420
- Unique references: 420
- Missing, duplicate, unexpected, or nonfinite records: 0
- Data-derived records: 126
- Frozen constant records: 294

## Custody

The private registry and local locator were written outside Git. The private authority was reopened and rehashed before the sanitized public receipt was written last. Registry, locator, public receipt, authorization, control-source, authority-definition, calibration-policy, and input identities agree.

No numeric calibration values, raw HAI values, labels, credentials, or absolute private paths appear in public artifacts.

Historical E1 and historical numeric-registry identities were not restored or reused. Utility remains unexecuted.

Next task: `TASK-039E3-R2R-UTILITY-NORMAL-ONLY-AUTHORITY-V1-MATERIALIZED-AUTHORITY-INDEPENDENT-AUDIT`
