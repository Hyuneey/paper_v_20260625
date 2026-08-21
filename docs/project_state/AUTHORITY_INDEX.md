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

## Frozen D0 PCA-SPE model and threshold — integrity audit pending

- Training Implementation Commit A: `34edab1dc148fdd82a050c3446e87d6eda4f95fe`.
- Independent Audit Commit B: `1041b6ed1efc335b8f5c5fe50dbfc22a87ec6d44`.
- Model/Threshold Freeze Commit C: `44ce989d7f50e2722eed70963e030ba1ba44fadf`.
- D0 design: `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`.
- Preprocessing content hash: `baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270`.
- PCA model content hash: `f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b`.
- Selected k: `10`; residual dimensions: `27`.
- Threshold content hash: `7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695`.
- Model receipt: `913f4a4bcf1771146f9493cded893b10eb97d2d177fe224f855c289d81ef1362`.
- Threshold receipt: `2ee6fc8aba25d23449c14b08deae2eca0c5b739f6a251e43ead41923c978d326`.
- Train4 sanity: `fb58290c1a59d164d9ace673968910db0f8ab65331ef3dfacd837c39685921ee`.
- Accounting: `ca7f038c1c91b24feee38101c9d8b19cfe97a3dc417c32cee879f47942eed5f4`.
- Readiness: `fcba1018b1e42ff7fdda9467a02a4f902ec6803486a3847675752508537cda29`.
- Bundle: `fa041f5e0006fc56665d22c82eb0fdea51917e573ffc4946c8a3f83bf4ada1e6`.
- Receipt: `b4142789cbe99513c1763df15e0207588b75453829d2abe1aba4eaa60da75357`.

The private numeric artifacts and their local bindings are not public. One
model fit and one threshold calibration completed with zero retries. Train4
was evaluated only after freeze and caused no change. D0 INNER, D2, and OUTER
remain unauthorized pending independent model/threshold integrity audit.

## D0 model/threshold integrity authority

- Audit Commit A: `0a5f8ef4a6eea38e2661fe2a6a3d24c849133f2d`.
- Audit Report Commit B: `0dd53fbbc36b0483d90a5161caab7946ddd6d1fc`.
- Freeze audit: `fb05a7801f312ce629f8d684939e4755f2c0773d8b661c95cf554b94d700cac8`.
- Preprocessing oracle: `c9cb4737e224b9a942b66f8267f5c9479dde4c6507b316553fe88db3c8f018c1`.
- PCA oracle: `e3bd67ebab5e90c431e5eb87ebc4400a203484d4eed1874675d0d3633ae5eea8`.
- Threshold oracle: `43ee484a9a0f0ebc03699ddf6e201ca8c085081d938f3774e293e26db00b06c2`.
- Train4 oracle: `57a1b8a8e55f61e1d50526028f5bbae965488c646f97d68fa6d3a2f3e88f05f4`.
- Readiness: `4849661e894bb3c6d31e3a97451ae3cb596bfb4cf231388514935e64ee460b19`.
- Bundle: `5769e397c078680ab66bff7f698ccbd0c65f929430465543320a06714b7707ce`.
- Receipt: `4a66590a223f17bf363521f1d2e5e2b8f184b85d43500a8f6683b88f9648119c`.

This authority certifies integrity and deterministic reproducibility only. It
does not authorize D0 INNER execution, D2, or OUTER.

## D0 execution-authorization contract and blocked custody attempt

- Contract Commit A: `4229e7c108c350174c03e4de0023ede3da8c1034`.
- Independent Audit Commit B: `c6481e201a11708ed0ef3d746e8057f627fb97d0`.
- Blocker Report Commit: `bb2e77c396bf321d61e1c9b7247582a0ccaa3636`.
- Blocker artifact: `480123d5398d064834ffe904c43611ec7043a1508581f5ec66487747dfb0a584`.
- Scope: `HAI_23_05_P1_TEST1_D0_PCA_SPE_INNER_V1`.
- Static gate: 90 tests passed; 88 independent attacks rejected; accepted
  invalid zero.
- Real preflight: one attempt, zero retry, failed closed before authorization
  because exact test1 feature and label raw custody were unavailable at the
  approved ignored binding.
- Authorization issued: false; D0 executed: false; D2/OUTER authorized: false;
  test2 access: zero.

This blocked artifact grants no execution authority. The next authority must
restore only exact official test1 raw-byte custody and must not parse test
values, retrain, recalibrate, or execute D0.

## D0 execution authorization after test1 custody restoration

- Historical blocker: `D0_AUTHORIZATION_BLOCKED_TEST1_RAW_CUSTODY_UNAVAILABLE`.
- Restoration Commit A: `1a7933b32be138eee1184cac9017ce24070882b7`.
- Authorization Freeze Commit B: `01cd15831246f94b2111fd3d9c0589e639f2d254`.
- Restoration report: `dc25f9aa51dc1a31d068110399dd29a7698f273d7cff9621f1634d7e16715ab9`.
- Fresh-process preflight: `033f1f9981bb5323e2830fa30d7e6613ce49b7a530e14a50ca2c4df75b848131`.
- D0 authorization: `a155fbb2659dc2a8b233db179706a13338a58ae41610f5c6db01f90f3b76a1ef`.
- Accounting: `98493fe49d1c816c713ae2068276717137d6bd321b92e65dd0b23e0ff91b47fe`.
- Readiness: `3a105a529fc1adbb85fae1d2a1cfe2a5777e858059ef7cd6a51651b8bea5b93c`.
- Bundle: `618f5add4ad13f8c999414add7a294ee25946323baa775b54e4b90838c97e1a0`.
- Receipt: `10540956fe37ccd025d82d1e7a7c61eef26d869c1e9f97c7bda9b2415d4e12f2`.
- Scope: `HAI_23_05_P1_TEST1_D0_PCA_SPE_INNER_V1`.

The exact official test1 feature and label raw-byte custody was restored with
no scientific parsing. All D0 private bindings remained exact. One new-process
preflight and one authorization issuance passed. D0 execution is authorized
but not executed; D1 rerun, D2, test2, retraining, recalibration, and OUTER
remain unauthorized.

## Frozen D0 INNER result — integrity audit pending

- Implementation Commit A: `c117087ec43d6e58167e77087e13b6a8a9226d42`.
- Independent Audit Commit B: `f45c71c9990984f6fa0c552060c8ab51e1e5c9a4`.
- Result Freeze Commit C: `78d758f50657413eed28dc838212be9a1edeffc7`.
- Committed execution grant: `ed2077cae7a770cf28f3a576ea9298f7c4530769c58521241b36ffcb213e9671`.
- Execution implementation identity: `8f00469a632643cd10cc4257f5d1fe380036c7763b03cb70b13d01815a287ee2`.
- DetectorPrediction artifact: `a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6`.
- Score evidence: `ee9acb8de899fb8aa13fa70d1675ad61862982ef20ab8815702c7a3c620be91c`.
- Private metric evidence: `628270f3413276d6d76c1ed3e1802679d37eae125898d250bb61524cba151176`.
- Execution run: `0593d05790fef3b9264af587c451ece6186db438541a8b14edabbb2ee4bdeeb9`.
- Implementation audit: `7ea381b8b1af3a792ef4a3f01c3d8b28644595b02da762bd8e102a1de981ac39`.
- Accounting: `5ea9f8e0963a7e268f010a74aecc4c2a13a5c0bc0986e583fdbcee3eddf7379c`.
- Readiness: `b25ec0663b8595cbbaff36c97b28e29a7364dc586adc0bfc8c7558f36de8ee18`.
- Bundle: `253b78a7a76f45669dd9289e931c2e8719c14bcc3bdc1723d222de23ea9e0a23`.
- Receipt: `62dab615ab8f95d7c65d4edfd605abd7543f28a09d54032b52ffd36f971b71da`.

This authority freezes the first and only authorized D0 INNER test1 result. It
does not certify result integrity or scientific interpretation. D1 remains
unchanged; D2, test2, and OUTER remain unauthorized. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-V1`.

## Frozen D0 INNER result — integrity audited

- Audit Commit A: `346a9f1ec6d5b1d97a66da45fcff66f44353742e`.
- Audit Report Commit B: `a1ff1929a86e95675431c2c32ace01efa2696a80`.
- Freeze audit: `8e22cb39ba038d3492592f4a3f91cbb64d2640d146dc615b35aab1137635fdc5`.
- Score oracle: `6c6e80549b9bc8f4e047c5db222af3de1647d7c0cee8684497d06eaff701df6e`.
- Prediction audit: `d76903177a1595870c841086aa0aa6debd302f679b71163fa4b38686975b37bc`.
- Label-independence audit: `9b57b0b7b8f40f2384dc7ce8d612ad5f4d24d954372fdeac6b6d13722b79014e`.
- Metric oracle: `89f7b33e89d24cab74a589ec0efdaaf2c47acacc1693fff24729151a7a07bfaa`.
- Accounting audit: `563bdecde07c2bf4c6d4543b2fa4d3dc42b250d7ff7e5e6bdd05c588fb138a89`.
- Leakage audit: `84221c711b1635f5c2f31f40c3eef11b39df2f05835cff657ac583b650abb645`.
- Independent audit: `d88148c61df8669a291d86e6f2bcd18838954f05b61d1f512ad05601db620361`.
- Readiness: `b18ccca46ed84e09aedeb258f6089e07444da0c108a60f4da3160fb3a521282d`.
- Bundle: `9b74f9c56571526870f274e0928516ce642e1bc0d692ee3cdd8dce0cceddafc7`.
- Receipt: `15559141048efd729b3b4645b4f0baa4ac6d07ceedb2417cbd7915f49435da70`.
- Remote state: `LOCAL_ONLY_NOT_PUSHED`.

These artifacts preserve the matched numerical and scientific audit evidence,
not detector quality or causal significance. Their prior final-certification
label is superseded by the strict report-custody blocker below. D2 and OUTER
remain unauthorized.

## D0 INNER result audit — report-custody blocker

- Blocker Report Commit: `69f902b380a2aa1b674ca70983bb131ad04f54ba`.
- Blocker artifact: `b59c6e23e0a3bc5dfcf89a2a0b67f78f581958055efdfcf0a78200ad9299ae01`.
- Blocker code: `D0_RESULT_INTEGRITY_BLOCKED_AUDIT_REPORT_SELF_HASH_MISSING`.
- Frozen D0 result mutations: `0`.
- Authoritative D0 audit executions: `0`.
- D2 authorized: `false`; OUTER authorized: `false`.

The numerical, prediction, label-independence, metric, accounting, and leakage
audit evidence remains unchanged. Final integrity certification is fail-closed
because the required Markdown audit report has no embedded self-hash and is
not hash-bound by the audit bundle or receipt. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-REPORT-HASH-REMEDIATION-R1`.

## D0 INNER result audit — report-provenance remediation R1

- Corrected base: `eea8a0d76420ba058df2789b914a6347255c0db0`.
- Historical blocker parent: `69f902b380a2aa1b674ca70983bb131ad04f54ba`.
- Remediation Implementation Commit A: `a0f74b2064a1fdf600e402f183fd2a9045a2183f`.
- Remediation Freeze Commit B: `4b7ab91529bd3ce19ee3e9b42db79ea04c7d8e3d`.
- Report hash scheme: `MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1`.
- Report self-hash: `fadaa840aedb5d2be96ea3a44ecb757e586578e4d25de2d2a82c244e7e8bcc51`.
- R1 readiness: `869fa95d7dd6282e45e73dfd6f5ad6b977747d7b63de1d65bdd0e933c10005e6`.
- R1 bundle: `ec25c4da9d162e1ca493332e5b8b51f40de6de2839afeb809a53781421ad6d66`.
- R1 receipt: `8f11f019f04e812f3a06f048b466256dfed0ad9b4b219ea033911a155b5d5835`.
- Remediation report: `2a6867dddb0e9a1d634fcb11556245a528f0607e985ccd9389bfaf4914d9a5f2`.
- Status: `passed_task039e3_r2r_utility_inner_d0_result_integrity_audit_report_hash_remediation_r1`.
- Scientific state: `D0_RESULT_INTEGRITY_AUDITED`.
- Remote state: `LOCAL_ONLY_NOT_PUSHED`.

The historical blocker remains part of the immutable authority chain. The
original report body is byte-identical, its single footer binds the R1 bundle,
receipt, and blocker, and all eight scientific audit JSON artifacts remain
unchanged. This remediation performed no scientific/private access or result
recomputation. D0 result interpretation is ready; D2 and OUTER remain
unauthorized. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-AND-FREEZE-V1`.
