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

## Frozen D2 detector-preserving corroboration design

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-AND-FREEZE-V1`.
- Base: `1c2f9a6272ee711b70b44ed79b9210af1026d3af`.
- Design Commit A: `8bb227521f28101970e7ea19ae97987d94b3c7c3`.
- Independent Audit Commit B: `03e58a79842d6f6aa0675595e6f78fca86b76de6`.
- Design Freeze Commit C: `5ad1c2fb56432be637c177cf64449238fdc1b504`.
- D2 design: `eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51`.
- Frozen D0 DetectorPrediction: `a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6`.
- Frozen D1 RulePrediction: `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`.
- COMMON-42 source mapping: `f8c47a212dbf65946f843f7fb0c737ae394a28c08af9ff18f5ac20a58d8891b7`.
- Design report: `74e6d66fc506cf9be0d40848d4f3d5b51b51f398ee0c8448c1453d5344bc0b94`.
- Input authority: `6b483f8007db86f910524fea6204a6119f82c23ff6fa24d1302fc93e98c58fb9`.
- Corroboration policy: `73069cade706c08065e4669dbe6b5c812f1e2d00d91d5e6ecc57e41d696a6751`.
- Metric policy: `a684368a13efe7699862cc626c4c6a28cb5eca342efe3cc3f4bb77adbfbaa012`.
- Independence: `4d684c5b2ea55ea6cd7280f5d64241b4f8483e4988319497388f193fd7db312e`.
- Independent audit: `55599576c754c31f00519823d73ded39c924a114ac5eb94d006bba77ddc37932`.
- Readiness: `50a9547cadf0b6dca779dea5f107c6368fdde7d4e1251253c9394e328c1d5aea`.
- Bundle: `2b75563a57d89816b2936d4172762b9d3bca0cf1c8752c780d9c5ecc89cec675`.
- Receipt: `d14feaa9a1fe402159806f29ef7499d9ca1e119902fbf1d12faad7b010b0e245`.

This authority freezes the D2 design only. It grants no D2 execution, D0/D1
rerun, test2, or OUTER authority. Exact next task:
`TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-AUTHORIZATION-V1`.

## D2 design provenance clarification R1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-PROVENANCE-CLARIFICATION-R1`.
- Base: `ea1dec8129b10d9941802359d2ab742d83d1f2ed`.
- Implementation Commit A: `cbc1da20ad3782e1a959aceaf42a8d779ba65167`.
- Freeze Commit B: `809efa1fe256f4c16a063b39288ecd21ae61f61a`.
- Clarification: `f0fbea249e11b6a3ae27a43b4b705d8537983511e2659d88f49b9c64dcf59e10`.
- Readiness: `41a6dcf3428de7fa02284041a958be5926829db3f7527ccc1cd1a5f850a94211`.
- Bundle: `b6e02a5319f78f15922a0d2f3239122ee11bcd33f6151ecfa80cc87741f63b83`.
- Receipt: `bf049094ce211e86db22bdbdcfe78adddff76e1935cab792e594b09cf554355d`.

This higher-authority addendum preserves the original design bytes and
semantics. It distinguishes process-level no-read evidence from project-level
prior knowledge: completed INNER D0/D1 baseline characterization was known
before D2 policy selection. No D2 candidate sweep, result observation, or
outcome-driven tuning occurred. The original independence artifact and this
R1 clarification must be read together. Test2 remains sealed, and no D2 or
OUTER authority is granted.

## D2 INNER execution authorization V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-AUTHORIZATION-V1`.
- Base: `0c7335e3c24958f178f527367c7d901c1804124c`.
- Authorization Contract Commit A: `a8679d1ddfca2d3e8885cffcc77ee699ae3401b5`.
- Independent Audit Commit B: `50ff882a19aafea7a015ad8be2f09ef150cd104f`.
- Authorization Freeze Commit C: `a412a0e7e893d23e7806e18831142f75cd5c0828`.
- D2 design: `eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51`.
- Provenance clarification: `f0fbea249e11b6a3ae27a43b4b705d8537983511e2659d88f49b9c64dcf59e10`.
- Frozen D0 DetectorPrediction: `a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6`.
- Frozen D1 RulePrediction: `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`.
- Source map: `f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818`.
- Preflight: `5ec6ce95c38cfe313034882e3a9020c3846f71b9e368676627ded9094a41ad8e`.
- Authorization: `b931d7bd89e923dc4d380e35ed2b3ff514679a701e0b94a75d426130a3c4427c`.
- Readiness: `72fe36cd9e5df8117c7db511c1ecd3c70c7d6dc0ec9db16f8c854baef0b05f65`.
- Bundle: `61c33e2652734726fe408d7254068121ce1af5ef5de9372242a9b041276ad00d`.
- Receipt: `7d372987043e65d3038d06f318f5426cefd9a3bfee55fb27851aded0c52e6137`.

This authority grants one future INNER D2 execution of the exact frozen
detector-preserving multi-source corroboration policy. It grants no D0/D1
rerun, label access before CombinedPrediction freeze, test1 feature access,
test2 access, OUTER authority, policy change, or result-driven modification.
D2 remains not executed. Exact next task:
`TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-V1`.

## D2 INNER execution V1 blocked attempt

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-V1`.
- Base: `1b71e35b4938942bdb92ebbc769d59c04c43cf37`.
- Execution Implementation Commit A: `315eb5b578301d57c6ab90c0c2398e3df3dec3f5`.
- Independent Audit Commit B: `cd220a89f37e0a3913124116f49a90e0518c8b46`.
- Blocker Freeze Commit: `f42e706f712616e23f7a86d86cc2bd6cfc6f4ce8`.
- Blocker artifact: `b721ddc45f0e7c97646b520eab9384d74c6c12231cb744c0f493fbf661111580`.
- Blocker report self-hash: `5e56f352c6495dde6bfe1f00a7a6dae6eb4c031008c54519924aa99992699c90`.
- Authorization: `b931d7bd89e923dc4d380e35ed2b3ff514679a701e0b94a75d426130a3c4427c`.
- D2 design: `eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51`.
- Frozen D0 DetectorPrediction: `a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6`.
- Frozen D1 RulePrediction: `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`.
- Source map: `f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818`.

The sole scientific attempt parsed each frozen prediction once and computed
the 54,000-row fusion, then blocked when private FusionEvidence persistence was
denied. No FusionEvidence, CombinedPrediction, metric artifact, readiness,
bundle, or receipt was frozen. Label access and metric computation were zero;
D0/D1 reruns, D1 metric reads, D0 score access, test1 feature access, test2,
OUTER, retry, result-driven change, and push were zero. The exception channel
exposed one private path. D2 authorization is no longer active after the failed
one-shot attempt. Exact next task:
`TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-PRIVATE-CUSTODY-BLOCKER-AUDIT-V1`.

## D2 private FusionEvidence custody blocker audit V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-PRIVATE-CUSTODY-BLOCKER-AUDIT-V1`.
- Base: `78639e1b8286b4ff16ac63530725a1ce3d1eb91c`.
- Audit Commit A: `316bc6086ea10712c2efebfac97287f082fe2575`.
- Audit Report Commit B: `c32246d0d4139e3fdb6ced98aeddbdcebfdc94cc`.
- State audit: `8480d931df6cab7dff59ffd58a24be7a37751ce99d5685353acbefee120704db`.
- Root-cause audit: `b936f646963be187cb96ab26c454e7ecfcac8fa01c445f548eae1f168bb2cd53`.
- Path-exposure audit: `71ae3e1f3a327a5bb2b342d0c00f1f39254b15a0d957c1682212285f54e4475a`.
- Residue audit: `81c7ac685596c0dc5eb2ca73140e278f1175127e85516aafaf90c482ff834c06`.
- Recovery eligibility: `b7a0137ac5b090fc51215044a1d8cd8a8d2c1518d96990e59656df4501ca3e8b`.
- Readiness: `0d63fb4be13583deef4c7fe6c013d89fdad06a2b3f25cfd016197b28aea2bee9`.
- Bundle: `bb0d0f3a41194a86022f0097161ff7094e6fd217b09ef983532fe5e784a1dd56`.
- Receipt: `45d3a318765e77ec15d68724aae72ec7b5d7aad6b15be78baa3ad39f6272e900`.
- Report self-hash: `8993a5db909d2c89db6d16999a0f2180f4b523c0c13c99e9d24bc7229be437c6`.

The audit proves that the frozen fusion completed only in memory and the
private atomic create failed at the parent permission boundary before any
CombinedPrediction, label, metric, or result state. The path disclosure was
ephemeral and has zero tracked occurrences; exact task-owned final/temp
residue and CombinedPrediction are absent. Recovery is eligible only as a
separately authorized transparent second total attempt under
`PATH_REDACTION_AND_CUSTODY_RECOVERY`. D2 remains unauthorized and unexecuted;
test2 and OUTER remain sealed.

## D2 infrastructure recovery authorization V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-PRIVATE-CUSTODY-REMEDIATION-AND-RECOVERY-AUTHORIZATION-V1`.
- Base: `ae566dae3124b352bdae85cc54a011adad6743f8`.
- Commit A/B/C: `7b749b68868193d2aed350f8ca0df91ff1dc807c` / `0399012e28f97226821d76b7b35d2980ba4ac6c8` / `4d24d72c8061d49c899bf3160781eeb86c8e7ac7`.
- Recovery authorization: `0faa5c58073da28b0a3e1e9c4267aa4c16faa7723becf5d01b5ec9c391b7b141`.
- Custody preflight: `945ff83f929d0f98ebc6ed942a0cbf1053dcb995fcc6ece40178793cc47cb917`.
- Path-redaction audit: `33cb00918b266132e3520b42c63abae799119759de75e4693d953394bb8a32e6`.
- Readiness/bundle/receipt: `e81e25d5cce2129c21b83eca588dc0ae7fdc56ccfad3b6d682c91bcaf61950dc` / `d5dbfae507b00698983dbe9da4ba9fe1ecc63f84dd79f694339786b2219f39f0` / `9b028b0132a179c12ed921207e1b20f149a10482834897f0dc9851cadde497f2`.
- Authority: one explicit infrastructure recovery attempt only; no scientific
  policy change, D0/D1 rerun, test2, OUTER, or third attempt.

## Frozen D2 INNER recovery result V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-EXECUTION-RECOVERY-V1`.
- Base: `adbac8a7b000fdf74d1d34fed920a6266e651926`.
- Commit A/B/C: `6c52bbe1ace8895a8b5b27527e4f9fe2ca01b3e6` /
  `9648f1d6415911800058b64f8084a2cfe1fc31a0` /
  `9078c4a1639c35d848cad28194fb4195eb5daca5`.
- Execution run: `64c9486d325b112198975d5d1c8b92c56213498a47fd67ba654257d99edf697e`.
- FusionEvidence: `f41d53b04ee33fcf719a442d707522438f0d4dcdfcc14eee3a416cc98267729b`.
- CombinedPrediction: `cf1005a03d98481b57c3ce2ad74db3e2e5d2dc3a1983d60e0aedb4f46c83b3f5`.
- Metrics: `dacf0c8c7e43b3f48bbbd635ad5c824a338ecf4e52476402ec244eef4012c84d`.
- Accounting/readiness/bundle/receipt:
  `1ad805908d46006108c55a5007436fb384babaf472c007af49b32f640878ed9a` /
  `8768e1daabe8517b1260a560f8c46a92816f8cc9198da328743892751c34540f` /
  `655ae56707220086d35781c1a7de25abd68549923fc9c7a54b25be38abe1a45a` /
  `c60d3d1707f4edb2332cfa57578a7f560c8369f2bb4f00600ac77b9896dfeb99`.
- Report self-hash: `66b04243c9c6833be4407bf6a0ae1804a4e764342c9ec9faf7d9f4d7766bf851`.

This authority freezes the exact recovery result after total D2 attempt two.
Historical attempt one remains infrastructure-aborted; one scientific
execution completed; result-driven retries and remaining attempts are zero.
The result is not yet integrity-audited or interpretation-ready. It grants no
third attempt, D0/D1 rerun, test1-feature/test2/OUTER access, tuning, result
modification, comparison, or remote egress. Exact next task:
`TASK-039E3-R2R-UTILITY-INNER-D2-RESULT-INTEGRITY-AUDIT-V1`.

## D2 result integrity audit V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-RESULT-INTEGRITY-AUDIT-V1`.
- Base: `33202f21d47b6bf29b12156374c9a7760f5c70f1`.
- Audit Commit A: `251fc953ad09f337a4e11bb956b3d1de1438e526`.
- Audit Report Commit B: `f7ae8f10e8e69e631c43184d6ea9cd3604829a9c`.
- Freeze audit: `ed2519a4023b6d258eaa8ad86f65b15e63c50336a8cf9b4f503027fd477e2496`.
- Fusion oracle: `0c3148c2f651f5707f5aa39ae018400653b7c375f027cddb8c06a223fb76feb5`.
- Prediction audit: `2bd70a56a7e9c5cfd255e54dda0d43697c7d5e3922d58a21e978614f74e2ea72`.
- Ordering audit: `e5b6511bbd32cdea1c082e9ae71d91c005e32ceb7c5e66e8752157cc7e2e78bf`.
- Episode oracle: `c20e9e32624950e786c055e6c2ba200ca20e78b06685812727e553e738f3f653`.
- Metric oracle: `d933d62b4a067e0f71f6dac22b11b32ff1811857b047fde9e4d1f7e947116483`.
- Attempt accounting: `668b33beaea66652752a4ea2df40bb3a4a64bb0cccc4b9371440da91cc929e21`.
- Private custody audit: `195f8aca72ba95c8c90af563725dd7b5dfba9adf6b970b514f7452c47b7cc8f0`.
- Readiness/bundle/receipt:
  `56e49e58eea4693bf23e2a8b0fb17851f68e679015aa84fbcc874ce07161111c` /
  `19ef39ab23c54f5e1c6a626f95f0e6d886e5fd22b7ac904e9221175d44477c91` /
  `c45db852c6d5571ec7930fc12d815b383a29e31939e711eb5f2e84c69807b448`.
- Report self-hash: `01f770f1a6304e1bbf5b43934a32bd44aee99cd7ac718d0b116e89908432bbed`.

This independent audit reproduces the exact frozen fusion, 54,000-row
CombinedPrediction, episode sets, and six metric values with zero divergence.
It validates both private evidence hashes and preserves the permanent two-
attempt history. D2 is interpretation-ready for the separate INNER scientific
comparison task. No execution, third attempt, result modification,
test1-feature/test2/OUTER access, or remote egress is authorized.

## INNER D0/D1/D2 scientific comparison V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D0-D1-D2-SCIENTIFIC-COMPARISON-V1`.
- Commit A/B: `f1d26f83ab5d13c28a7f82909c4ae7e69d3b7aaf` / `f4e21a2a73adad16bd15898cbb5c01bb19646ba3`.
- Arm metrics: `4704d3a526eab806ece1c511094fc2d2798ff63bac537273d35811ce4e9bbb81`.
- Event overlap: `51589bbf1bd90b2f04504595af465eb7e514061ef21d16ad731e02508072f1b3`.
- Recovery analysis: `32f008bfbcc0d1eea3efa3f27d6684823f6a02c1eab7b38333544198adc6892a`.
- False-alarm tradeoff: `fc283c58c0426e85c16eef299d339f672170df6d97423e6f013b7bc36fa30a17`.
- Interpretation: `c9516ad8233ab8d181f04f7f486bc04cb5073d80f90e3b51d004f9a1a7890885`.
- Outer disposition: `5b9a96901e70ebc94edaebb8f7ebf78a4911af9a5da796a6df3febbc2c7b726b`.
- Receipt: `d444ed1f7979270b945c03f2656b92e8ef7ebf8e98eca2f88f976999da00216e`.

The comparison freezes the negative D2 V1 INNER result without redesign:
D1 covered all three D0-missed events, D2 covered none, and D2 added three
normal false-alarm episodes. OUTER remains unauthorized pending an INNER
failure diagnostic.

## D2 recovery-signal failure diagnostic V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-RECOVERY-SIGNAL-FAILURE-DIAGNOSTIC-V1`.
- Commit A/B: `78e016d4ff781581d998b445022dd2c35f61491a` / `0c40a0118c1c5f14cf3ca2d42178c34875d4dbed`.
- Recovery events: `b889b03655e00fdb71d9103a6217ec63719a17d058dc247d915e1783b008dd29`.
- Temporal structure: `e60b102048cf3ecf25cba4fc8f1137ec6f15cc198728202406a60f0859a113cc`.
- Source multiplicity: `25a462895d92885e23a645bb0468c24cf4415deabd6699f7580a16c027e2d7d4`.
- Normal reference: `b5d0ab43dad80a6903bd18e1a49f0c7566ed9a8a3c75ce5fe238d9480a136985`.
- Gate failure: `b006b4c79262906087b7a5c52160b9a09926318776339940018d56b3077ef96a`.
- Redesign disposition: `2792aec7adddf63244ef6547fa90d106bdbcdcac242bc28ef6fa36d52c18b85e`.
- Receipt: `58b0a68ad4a9e4e6938e14d031ae8f6e80a7e75a071081e651ac33e5f6872f0e`.

Mixed single-source and cross-source temporal desynchronization prevented the
three recovery events from satisfying the exact gate. Redesign is justified
but not authorized. D2 V1 remains the immutable negative baseline; OUTER and
test2 remain sealed.

## D2 V2 native-horizon design V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-V2-REDESIGN-DECISION-AND-PREREGISTRATION-V1`.
- Commit A/B/C: `d4846fea19aa69cb31bbf80eb4f6c6ce21ae366d` /
  `784deb8a9042b14e603d675e22ab31b8c89c7ac7` /
  `52b195fd6fd593160118388a36a7c1f77072c1df`.
- D2 V2 design: `ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4`.
- Native horizon map: `e9825a578495396d935397e79d8c50717dccb47f069f13e93f6306f992a9407c`.
- Design/input/horizon/token/corroboration/metric/provenance/audit hashes:
  `cf68f4bb6a9eac5a717d3fd644a40a073478afc5c859dd6b41531192226fa8d0` /
  `28dbbaef220962c70efdab9a607d47459c07006c5cc580b4ebd1b72eb7c44a83` /
  `14aa91ff3f976fd86eca09c379ff10096fa7aae424ed4f926421888664c5eb8e` /
  `19324935f972ccc842a47d230dcc8e7328cd595d4c5e4cfe78de62bb286d3f61` /
  `ff64bfe98d32920305e759b4cf198355dfd96d7d56b25e341128d921a84cb726` /
  `90c09592c524578332d13868770d70e887e7078c37eafe72bf43dd84d441811b` /
  `a81bbf793d3e27ec67184887fb72938df11c209d7c2c0627972c13e584105676` /
  `f613cad8feb501814c9a56fa912c4d7145491b83b81fcb2ce34cd17355ba866e`.
- Readiness/bundle/receipt: `073df848a77991e7f6d0138d5e6978230c46358250348b00d39f7d4364c15707` /
  `4e44860a3e3357965ec1ac04f5817ceefe90f41fe01fe6b86dac47d64b23fa6e` /
  `df98ca12e6a83c5ae9d73c80f7a26f0b1189a3743101d5342ed908017304dd7f`.

The authority freezes one causal, detector-preserving V2 policy using each
relation's already-public native selected horizon and two distinct active
sources. It authorizes no execution. D2 V1 remains immutable; labels were not
reopened; test2 and OUTER remain sealed.

## D2 V2 INNER execution authorization V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-V2-EXECUTION-AUTHORIZATION-V1`.
- Contract Commit A: `ab1773f3d898e98ccb45585434e7fd0053366af9`.
- Independent Audit Commit B: `1a8dc972f1e267c53d143d6623c92dbaeb0249f1`.
- Authorization Freeze Commit C: `867738a3904d2bc110865df5dfe4f9fe3032eddf`.
- Version: `TASK039E3_R2R_D2_V2_INNER_EXECUTION_AUTHORIZATION_V1`.
- Scope: `HAI_23_05_P1_TEST1_D2_V2_NATIVE_HORIZON_CORROBORATION_INNER_V1`.
- Authorization: `0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45`.
- Contract/native-horizon/custody/path-redaction/independent-audit hashes:
  `89e4e2bdf91cea0ab5d67827945c0051c812d3740f8cbe038a078f601a19caa3` /
  `2893972703172965caea957f8f7dbd0b8b89a1ce14f7e559b1ef606404d90d25` /
  `1296c76458d498d0e35b209c4da9691f6d02e1899778906409d96d7c18d4e463` /
  `1b51853f796b01fa0fa47c5c1a431c6d79997a62612b4569ba9a255045ca4355` /
  `3ee5e6a3deefaa39365e9eb471789a0cde2cf60e4635b1743a176d45b48f9ee8`.
- Accounting/readiness/bundle/receipt/report:
  `33239fd17c0266f4e18a1079a37560d16dd5143dd64062092a86ca27cfbbb419` /
  `02ce6ebb6d71225160210772768a6f6a904a6df6f188ef7a7b47fe034bdf922a` /
  `779a326715bbf5f7cebc94c06ea24b1b4538b75abb2117281a01cb65ec784472` /
  `16198e7d11b241977031c73dd8ab3fb645c4620e75f446e6c57793ff49693b96` /
  `40f63c01c8594f1ff4fbdd76d1373001191b1a408d96000f0707ebe6dc890830`.

The grant binds the exact V2 design, immutable D0/D1 predictions, COMMON-42
source map, 42-entry public native-horizon map, causal token policy, two
distinct active sources, D0 preservation, and prediction-before-label order.
One non-scientific private sentinel and one raw label hash passed. No scientific
prediction parse, token construction, fusion, metric, D2 V2 execution, test2,
OUTER, private-path exposure, or push occurred. Exact next authority is the
single D2 V2 INNER execution task.

## D2 V2 INNER execution V1

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-V2-EXECUTION-V1`.
- Commit A/B/C: `2bbb3dcaced47c8d15337e45eb0e0b741c1a3ed1` /
  `b3acf3cbb0b6bcb21548daa319fd37923357b952` /
  `55d41c543e110a9a6f0f5e2e2671857dba938aaa`.
- Execution version / implementation:
  `TASK039E3_R2R_D2_V2_INNER_EXECUTION_V1` /
  `9016e5c8be9fa0e56af6a5d1870617f1937e557b7eabd0afa5b20722e89ded62`.
- Authorization / committed grant:
  `0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45` /
  `9136c3b5432d471181765848619771f5234fae1d1a0c22d60eb584d3b8617392`.
- FusionEvidenceV2 / CombinedPredictionV2 / private metric evidence:
  `9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb` /
  `31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3` /
  `3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513`.
- Public metric / implementation / accounting:
  `8fabdccc0c9a9b502497aa58163131647303d5e27acefb995a06ca9d43850ba7` /
  `fe601aaa195222470e8e746a6c9ba318b338172bc750bff1194bd4164f201ea1` /
  `7059e2b4e54ec53d0b72c072c71487b19efe056ce382357615dc152bf2382aca`.
- Execution / readiness / bundle / receipt / report:
  `c41957d8e9805afe0e39a0b28b01faaf8fa2ec82d8e4774083f6d7881d5036fc` /
  `59246da5731bad310c588945326a9f5d44ed9394ed7bf1312086f043566e37bc` /
  `ded276981ce75ebe5e947bd7a409d14b03208e7e23f1c8e3ddc1cd3070cb915f` /
  `e6f10713d467c4733422f5d4d548035f20b0ebc7e9e10e6ed3d73506375509bf` /
  `e45479ec778414a7e4a3d21b348f898176584abad7f2271baec5f34a21bb6fd6`.

Exactly one V2 execution froze 788 causal evidence tokens, 1,335
corroboration points, a 54,000-row label-blind CombinedPredictionV2, and all
six preregistered metrics. Result magnitude did not alter the policy. Zero
retry, D0/D1/D2 V1 rerun, D0 score, rule reevaluation, test1 feature, test2,
OUTER, private leakage, result-driven change, or push occurred. Result
integrity remains pending; the exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-V1`.

## D2 V2 result-integrity audit — fail-closed harness blocker

- Audit Commit A: `5374cc8293ce970738f2f3320abdbf1d9fbdb150`.
- Blocker Freeze Commit B: `e54abe8a2170b48e7eb437b4a4935c32e6cd9341`.
- Blocker:
  `592344d430b50724a7ae4f81ed0e73423ec1473586d0d9a15d2ff68f6009f879`.
- Code: `D2_V2_RESULT_INTEGRITY_AUDIT_BLOCKED_EXACTLY_ONCE_ORACLE_ACCOUNTING_EXCEEDED`.

Two audit-harness preflight defects surfaced only after independent prediction
and authority reads began. Exactly-once audit accounting can no longer be
certified in this task. The frozen D2 V2 result remains unchanged; labels,
test1 features, test2, OUTER, and authoritative executions remained zero.

## D2 V2 result-integrity audit harness remediation R1 blocker

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R1`.
- Harness Commit A: `e04ca7e7aee472c5450363f9a5e4a6a3fe2a6ef4`.
- Blocker Freeze Commit B: `a4968c2d8af89232d141826e10bd5145567407a2`.
- Blocker artifact:
  `dc6d83a33bdf985389b6d2d1b75e54f2b703e59f515369dc41b5a499280b0990`.
- Blocker code: `D2_V2_R1_PUBLIC_AUTHORITY_REJECTED`.
- Classification:
  `AUDIT_HARNESS_PUBLIC_AUTHORIZATION_SCHEMA_REPLAY_DEFECT_BEFORE_SCIENTIFIC_PARSE`.
- Historical blocker preserved:
  `592344d430b50724a7ae4f81ed0e73423ec1473586d0d9a15d2ff68f6009f879`.

The sole R1 process stopped before D0/D1/source/horizon/CombinedPredictionV2/
FusionEvidenceV2/label/MetricEvidenceV2 semantic parsing. No retry occurred.
The frozen V2 result remains unchanged and unaudited. Exact next authority:
`TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R2`.

## D2 V2 result-integrity audit harness remediation R2 blocker

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R2`.
- Harness Remediation Commit A: `b14cb96a19f6474d9c10e02abbdfedf3dd7c7a73`.
- Blocker Freeze Commit B: `1effce0b691b870c93e5195d930a26ec9ae92658`.
- Blocker artifact:
  `4e6526e382dbb0bf15bae9123eeeba3a090dcb59bfd767f3b19172fe3e353c0c`.
- Report self-hash:
  `ce0e3d5e7db0ba135989beeab97beb97f024ccfc5f5341a548fd33aa68fd04d1`.
- Blocker code: `D2_V2_R2_AUTHORIZATION_REPORT_CHAIN_REJECTED`.
- Root cause:
  `R2_AUTHORIZATION_REPORT_BODY_HASH_VALIDATOR_INCLUDED_ONE_FOOTER_SEPARATOR_NEWLINE`.

The frozen authorization report is valid and unchanged. The sole R2 process
stopped before all scientific semantic parses; no retry occurred. Exact next
authority is R3 report-provenance separator remediation only.

## D2 V2 result-integrity audit harness remediation R3 blocker

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R3`.
- Harness Remediation Commit A: `10f6b179438e70646ff94ca82fdc96ac63d2ba4a`.
- Blocker Freeze Commit B: `1d7a189755a70fabfbd00e66c320373b0ae05f4b`.
- Blocker artifact:
  `2baed348b67ec7567ea57d1892c4e605728120e65480728ca562528c822e9f4a`.
- Report self-hash:
  `e20b49b6f6b6f22eb3f40b9433710ba85df37893677941debfdded84adab33a4`.
- Blocker code: `D2_V2_R3_REPORT_PROVENANCE_SEPARATOR_NOT_CANONICAL`.
- Root cause:
  `FROZEN_AUTHORIZATION_REPORT_RAW_BYTES_USE_CRLF_SEPARATOR_WHILE_R3_REQUIRES_EXACT_SINGLE_LF_SEPARATOR`.

The R3 public gate rejected the committed CRLF separator without normalizing
it. Authorization identity and JSON chain passed; all scientific semantic
parse counters remained zero. The frozen result remains unchanged and
unaudited. Exact next authority must explicitly reconcile stored report bytes
with the frozen body-hash writer convention in R4.

## D2 V2 result-integrity audit harness remediation R4 blocker

- Task: `TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-HARNESS-REMEDIATION-R4`.
- Harness Remediation Commit A: `bd0599c6bb6b377d34147a2ede490be061421c9a`.
- Blocker Freeze Commit B: `f40f2539782af78d5808835da1159b81075cde69`.
- Blocker artifact:
  `34acc0c252b13054b15f3ac6fb1a560fdf0c653f2580305c9d582f6a52e863fc`.
- Report self-hash:
  `56430aecc90244483cac4f58ef521dfd3e826b9be7fd2df5ca5246847e7c99d0`.
- Blocker code: `D2_V2_R4_BINDING_REJECTED`.
- Blocker class:
  `LOCAL_PRIVATE_CUSTODY_BINDING_REPLAY_REJECTED_BEFORE_SCIENTIFIC_PARSE`.

The sole R4 process passed the public authorization and Markdown provenance
gate, then stopped at the local private-custody binding replay before any
scientific semantic parse. R4 was not retried. The frozen V2 result remains
unchanged and unaudited. No successor task is authorized pending explicit
custody-binding remediation authority.
