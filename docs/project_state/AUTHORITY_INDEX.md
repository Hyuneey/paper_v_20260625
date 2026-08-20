# Public authority index

This index contains public identities only. Exact committed receipts and
reports remain authoritative.

## Evaluator and protocol

- R3 implementation identity: `af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5`
- R3 independent receipt: `6f671aff17ea193ebf862af0739ee0bee22634f3f337944c14c90172acde34e0`
- R3 completion audit: `2992599eed2d2205bd9e2192515dff47168386281da865c511fbadb1bf55a1a7`
- V4 R1 authority: `1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343`
- Portfolio: `COMMON-42`; relations: `42`; T2 authorized: `false`.

## Numeric and source-census authorities

- MAIN descriptor: `665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928`
- MAIN reference set: `d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae`
- MAIN references: `420`.
- Supplement descriptor: `d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927`
- Supplement reference set: `5139cae6e454318f0ca4317f3f5eaa5f775bd4f75261c4110ea610815929b580`
- Supplement references: `6`.
- Combined source-census contract: `cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9`
- Source coverage: 9 MAIN + 3 supplement = 12.

MAIN is relation-execution numeric authority. The supplement is source-census
isolation authority only; the two are not an interchangeable 426-record set.

## INNER data authority

- Dataset manifest: `5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2`
- INNER split: `30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0`
- Test1 feature expected SHA-256: `78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be`
- Test1 label expected SHA-256: `eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc`

No locator, registry, dataset-root, private registry content, or numeric
threshold is recorded here.

## Reproducible HAI INNER materialization

- Strategy: `PINNED_OFFICIAL_SOURCE_REPRODUCIBLE_CACHE`.
- Official repository: `https://github.com/icsdataset/hai`.
- Pinned commit: `2a814cebc9a66b06c9e5cd545e2d72e65d383737`.
- Frozen official fallback metadata:
  `a7389cc123a544302b896c4c1ffc931a3c61c22318c0fa53c575cd1567d5fbfe`.
- Frozen byte-equivalence receipt:
  `7917f8736c119e774a945096f41f8abc18bce30267dd9e754c5a20157a5bf7a8`.
- Materialization report:
  `42c030775435a00ce127504d59de9767a85ed0bb612b4c3f024af8054764851d`.

The cache location is disposable private machine state and is not authority.
Only the frozen source, commit, payload allowlist, hashes, and sizes are public
custody identity. This materialization does not itself grant execution.
