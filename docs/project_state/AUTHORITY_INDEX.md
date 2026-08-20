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

## Portable private custody control

- Control revision: `R2_PORTABLE_PREFLIGHT`.
- Locator policy: `PORTABLE_PRIVATE_LOCATOR_POLICY_V1`.
- Locator policy hash: `371386b03185a5642e8f6bfd04bc2f39c9e10aa6396dbaf6909d941bda72e6cd`.
- MAIN recovery strategy:
  `DETERMINISTIC_NORMAL_TRAIN1_TRAIN2_REMATERIALIZATION`.
- Supplement recovery strategy:
  `DETERMINISTIC_NORMAL_TRAIN1_TRAIN2_REMATERIALIZATION`.

The frozen registry content hashes are portable scientific authority. Local
locator self-hashes are machine-specific custody metadata; historical locator
hashes remain provenance evidence only. Every fresh locator must still be
canonical, self-hashed, outside Git, non-symlinked, and bound to the exact
validated registry and materialization authority.

The bounded R2 remediation supplies the frozen executable-equivalence and
construction-evidence documents explicitly to the unchanged canonical MAIN
registry validator. Its issued INNER D1 authorization is
`deb08014de20c398d2dcde046e14b505a65af2d52cb6eb309fc8188f020b5834`,
bound to custody preflight
`3acff12cb2135b86539720e792d6e01075808ea84b6939b06909d397b1b43129`.
This grants D1 Rule-only INNER test1 only; it grants no scientific result.

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

## Frozen INNER D1 result — integrity audited

- Execution Bridge Commit A: `936296cdcf9f5d87658a0c9993856ccc7d9222b2`.
- Independent Audit Commit B: `c880042d1a49c12e2a6788d618bfb9b5491e1be0`.
- Result Freeze Commit C: `9fe9192c6da4e2d1f3c7a42ecdd28006e8534449`.
- Bridge identity: `959de0f2ed781f404f583af75f7938bda56634024ddfbf23ecc9c38f5704edfe`.
- RulePrediction artifact: `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`.
- Metric report: `b11a785dd243f30cac8820c49b978e194d993282c728537137b6a803b16d70d1`.
- Execution run: `97bc0ef15508957d32427188205d7446fa58bc2234cade577d0bc93c3ce52e73`.
- Readiness: `c76281465c61165a6b444fd3dc52b235379795a7129ab397e9e339cff46d87ed`.
- Bundle: `361a9605279c46d66a69055904ee06f4266f5a29b30e5f6a1e5a81d2335c4f4e`.
- Receipt: `0966c35ec6865ed9f97651092876b2ff67322f59daa8ff09a425614d28b74c8e`.
- Result-integrity Audit Commit A: `470b5ef7e51d26cc0fc947a6a37ab23d21860538`.
- Result-integrity Report Commit B: `fd54c5cab69927e91d268f344c54f6614f28021f`.
- Result-integrity readiness: `8c6eb7f7b099bc48537c78cf7cb5510dbf599dfd58c37efc44705a6a9fd0f5be`.
- Result-integrity bundle: `e38b56e877842c1678fccaea0e23e5e1c761265534ff9fe8ccc0f5c24552c4db`.
- Result-integrity receipt: `1f42fecce799f09e2dfd73b2bc041f7f7bafd60522d95c004f27aa35b7846a4f`.

The audit certifies that the exact frozen D1 result is internally consistent
with its authorized execution protocol. It does not certify scientific quality
or deployment value. D0, D2, detector, and OUTER remain unauthorized; the next
task is independent D0 detector-baseline design and freeze.

## Frozen D0 reference-detector design

- Detector ID: `D0_PCA_SPE_V1`.
- Family: `PCA_RECONSTRUCTION_SPE`.
- Design hash: `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`.
- Design Commit A: `4bdb16701a84b383f713629524a20900bba27d95`.
- Independent Audit Commit B: `4e4e904cca8779e5dde62bcea697e6d40d58a867`.
- Design Freeze Commit C: `2528632fca2c64e1bd4a293d57bed56cc3e5665b`.
- Feature count: `37`.
- Feature set hash: `6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515`.
- Feature order hash: `a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57`.
- Readiness: `533e62761efce660e1d10726268187c2a9ba5e0d2b0763814b64bd75b0473c4e`.
- Bundle: `8fa5ab4b81a4dad0f7d1d13bd356b3aad21a45e747cd3b047ada697450ce3034`.
- Receipt: `61299eba73c09faaf9396a6174ad487e4736c6271e274a2c18dd3cb60fd0c8b5`.

The design fixes normal train1+train2 model fitting, normal train3 empirical
threshold calibration, train4 sanity-only evaluation after freeze, population
standardization, deterministic PCA at the `0.95` explained-variance target,
SPE scoring, alpha `0.001`, and strict `score > threshold`. It performed no
training or execution and grants no D0, D2, detector-runtime, or OUTER authority.
