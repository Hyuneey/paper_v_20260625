# Project handoff

## Current authority

One sealed OUTER confirmatory execution of exactly three frozen arms is
authorized but not executed:

1. D0 detector-only (`D0_PCA_SPE_V1`)
2. D1 Rule-only (`COMMON-42`)
3. D2 V1 combined (`D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1`)

Authorization version:
`TASK039E3_R2R_OUTER_D0_D1_D2V1_EXECUTION_AUTHORIZATION_V1`.

Authorization scope:
`HAI_23_05_P1_TEST2_D0_D1_D2V1_CONFIRMATORY_OUTER_V1`.

Preregistration / authorization SHA-256:
`66179921042faecf189fe93ddaf20bb06669afa6e27dbefb67c9b95eabb93427` /
`fb8abb3a342c591873d15d4bcf28cbdcc7363fce77a228f486f122ef5933ac14`.

Canonical receipt:
[OUTER authorization receipt](../task_reports/TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_V1_RECEIPT.json),
`1ef346ec824561def8d09c8c09211c11fa2eb5c2bb415c95d2008b4af6a03d4d`.

## Frozen boundary

- Dataset manifest:
  `5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2`.
- Test2 feature / label manifest SHA-256:
  `b2b8dd295aefd87e39260fe43cb4c73ee86d6264b0ac4b0761e7efb0c2b545c3` /
  `8090c44981176e39b0f01a7126a80248ac0b93355c00f9db4d4e2f2106452b92`.
- Expected test2 rows: `230400`.
- D0 design / model / threshold:
  `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174` /
  `f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b` /
  `7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695`.
- D1 construction / descriptor / evaluator:
  `1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343` /
  `665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928` /
  `af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5`.
- D2 V1 design / source map:
  `eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51` /
  `f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818`.
- Corroboration: at least `2` distinct sources at the exact same physical
  second; D0-preserving; no tolerance, native-horizon memory, D0 score, or
  label-aware fusion.
- D2 V2 authorized: `false`.
- OUTER attempts / retries authorized: `1 / 0`.
- Post-OUTER redesign authorized: `false`.

This preregistration task opened, hashed, and parsed no real test2 feature or
label file and executed no scientific arm. Test2 remains sealed until the exact
execution task replays this authorization.

## Exact next task

`TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-EXECUTION-V1`

Do not start result-integrity audit or final synthesis before that execution
freezes its result. Do not push.
