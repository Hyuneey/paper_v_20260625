# VALIDATION V2 Normal-only HAI Custody Recovery

## Verdict

`NORMAL_ONLY_CUSTODY_READY`

The historical `BLOCKED_NORMAL_DATA_NOT_FOUND` record remains valid as an
execution observation. Its corrected root cause is
`HAI_CODE_MATERIALIZATION_POLICY_NOT_PROPAGATED_TO_V2_RECOVERY_LOGIC`, not a
failure by the research owner to provide data.

## Permanent recovery policy

- policy: `DATA-POLICY-001`
- acquisition mode: `CODE_MATERIALIZED_OFFICIAL_DISTRIBUTION`
- official payload route: `icsdataset/hai-security-dataset`
- identity authority: pinned official Git snapshot and Git-LFS objects
- user local path required: false by default
- next action: `CODE_BASED_MATERIALIZATION`

The approved code materializer created an ignored private binding for an
external cache containing exactly:

- `HAI_TRAIN1` → `hai-23.05/hai-train1.csv`
- `HAI_TRAIN2` → `hai-23.05/hai-train2.csv`
- `HAI_TRAIN3` → `hai-23.05/hai-train3.csv`
- `HAI_TRAIN4` → `hai-23.05/hai-train4.csv`

No user path was requested, inferred, guessed, or printed.

## Provenance readiness

Public authorities provide exact HAI 23.05 split identities, byte sizes, row
counts, the 87-field raw-header identity, ordered 37-feature P1 contract, and
file-local strict one-second sampling contract. The single runner must reuse
the existing official distribution, byte-equivalence, and provenance controls.

The recovery stage must apply the exact allowlist `{train1, train2, train3,
train4}` before any candidate stat or open. `test1`, `test2`, held-out, outer,
sealed, and label inputs remain forbidden.

## Result

- custody binding issued: yes, for exactly `HAI_TRAIN1` through `HAI_TRAIN4`
- private manifest created: yes, outside Git
- byte equivalence: `PASS_ALL_FOUR`
- schema identity: `PASS_ALL_FOUR`
- public materialization receipt: `receipts/HAI_NORMAL_ONLY_MATERIALIZATION_RECEIPT_V2.json`
- public custody binding: `receipts/HAI_NORMAL_ONLY_CUSTODY_BINDING_V2.json`
- test1/test2/label/held-out access: 0
- EXP-01 execution: not started
- EXP-02 execution: not started
- PILOT V1 impact: none

## Resume authorization

The resume condition has been met. EXP-01 and EXP-02 may now use only the
operations permitted by the public custody binding and their unchanged frozen
preregistrations. test1, test2, labels, and held-out inputs remain forbidden.
