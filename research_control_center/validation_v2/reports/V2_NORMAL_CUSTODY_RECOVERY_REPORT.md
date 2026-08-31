# VALIDATION V2 Normal-only HAI Custody Recovery

## Verdict

`BLOCKED_NORMAL_DATA_NOT_FOUND`

This means no approved locator is configured. It does not establish that the
files are absent somewhere on the host.

## Locator audit

- approved environment binding `HAI_NORMAL_ROOT`: absent
- active worktree ignored local custody binding: absent
- primary repository ignored local custody binding: absent
- host-wide search: not performed
- scientific candidate stat/open/hash/parse: 0

The only allowed safe layout is an explicitly bound external root containing:

- `HAI_TRAIN1` → `hai-23.05/hai-train1.csv`
- `HAI_TRAIN2` → `hai-23.05/hai-train2.csv`
- `HAI_TRAIN3` → `hai-23.05/hai-train3.csv`
- `HAI_TRAIN4` → `hai-23.05/hai-train4.csv`

No path was inferred, guessed, or printed.

## Provenance readiness

Public authorities provide exact HAI 23.05 split identities, byte sizes, row
counts, the 87-field raw-header identity, ordered 37-feature P1 contract, and
file-local strict one-second sampling contract. The single custody issuer may
use these controls only after an approved explicit locator exists.

The recovery stage must apply the exact allowlist `{train1, train2, train3,
train4}` before any candidate stat or open. `test1`, `test2`, held-out, outer,
sealed, and label inputs remain forbidden.

## Result

- custody binding issued: no
- private manifest created: no
- public-safe blocker receipt: `receipts/HAI_NORMAL_ONLY_CUSTODY_RECEIPT_V2.json`
- EXP-01 execution: not started
- EXP-02 execution: not started
- PILOT V1 impact: none

## Resume condition

Configure an explicit authorized `HAI_NORMAL_ROOT` or ignored local binding to
the parent of `hai-23.05/`. Then rerun the single custody issuer. Do not change
the frozen EXP-01 or EXP-02 preregistrations.
