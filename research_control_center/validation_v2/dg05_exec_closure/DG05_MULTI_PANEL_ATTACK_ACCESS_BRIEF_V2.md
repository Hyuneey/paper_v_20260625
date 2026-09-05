# DG-05 V2 — Multi-panel executable attack-access decision brief

Status: `DRAFT_PENDING_INDEPENDENT_EXECUTABLE_QA`

Decision requested: `DG-05 REAPPROVAL — EXECUTABLE V2`

## Why renewed approval is required

DEC-029 and the V1 brief remain historical. The attempted execution stopped before Phase A because the executable authority chain was incomplete. This closure introduces new executable hashes for projection, prediction dispatch, full process scope, P1 custody, scenario/denominator/result construction, and independent result replay. Historical approval is therefore insufficient and must not be silently reused.

During closure:

- attack/test payload accesses: 0
- labels/scenarios accessed: 0
- real eligibility generated: 0
- provider calls or credential reads: 0

## Unchanged scientific authorities

- Preregistration V2: `cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61`
- Method bundle: `dab320da47489e5093862b7c4675523c3e6b710faceb753e7f39c8e56f002fe2`
- Metric authority: `1222d0c7431376dbfa77451875f811123f41af881ae1472b30cd4a2e0f1f0776`
- Statistical authority: `cf90fee47e9294873e09aa516df8163328ee924d756c66b18a811c4ea2f9b463`
- eTaPR authority: `5381ceb1f19f25354a8feb36488dfaa85d3f2945770dc352f2bf8c18fd86cae4`
- Fusion policy: `587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc`
- Attack file census: `5018ba8d01e32a8a2ff4cf95cdb6ca75b51b006b812acf5cffe2b1d26b8a6a16`
- Attack feature allowlists: `e49ba9ee3f6a2f1273666c41ac1584636a53d5b4334d6cb95e3eed0b17a2764b`
- HAI23 portfolios: T0 `d95c0bb8234304f2b769e088f4399b6c071b2156982c9e1fadd175dbab5dba02`; T2 `bc2b5996989228f198dbcbf38cbedaf38516366f55d5011978ecda94ccf699b6`; V2A `ec0b3e2a32d457287cb8b101bec39059e99335be3fd85a3d1fb98668224c52aa`
- HAI22 portfolios: T0 `94f130408361e6b4a8051ed4a72a0ad385e90cb3212e2bf0d27af300f481503f`; T2 `b58313cd142256d000f89fd4a40512763b35e6b50752229109646bafc243fb5c`
- HAI21 portfolios: T0 `f9cad3c00c422614012b2147f3c21951632f8738ce2d8f9f1108d61ae69d6ef3`; T2 `9815c9a66debed593e21364377113d18422a840389d306a4a7648d5f035599dc`

## New executable authorities

- Executable closure pre-QA: `4fc3cea754bb36cac84569eca485b8f2deac519b87d80f0db71975f1b55b7e24`
- Approval manifest: `586202aedc3ea7996646035f29ee5c6fa62824ed4c0a255cd6bff17f0202ac42`
- Full process scope: `0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619`
- P1 eligibility custodian V3: `f688fae22866ac5bac7ac4517fd9171d7f0d907044f3afee9cd7a609a8919166`
- Detector subauthority registry: `c5f3f834435af6615e120f57c68c5d47eb66be8c07c4870c9f5fb0ee9cd832bb`
- Rule-runtime subauthority registry: `074768ef863e481482337df4af16ee12c5ef36fb52c2129417d0ad39aa98dd14`
- Exact dispatch registry: `246e19e4c9bcd81f8e139bd5ac609dac6db8a98add16013e1205641bb0c03433`
- State machine: `71e0febb462aa0580799781b9e8f2605ca944da3285f2720896dadb88a734beb`
- Production projection/prediction adapters: `fdbd373815c09e042c4cce0edaa2541a7cca7a46874f268481799db8a72539cb`
- Expected cell census: `87167612f6efa76b678334f7df66400a1fed40ee2264952f416b730f1836c009`
- Synthetic end-to-end rehearsal: `f273488e06465d6d3e2134093ab7990909bfc2e3f432418a0d47a43503695565`
- Nested byte-replay bundle: `2f260ddeb5e64177578d140f7ce573921c4ff43cbe9886cbfddc8fe7d99a3f01`

## Proposed two-phase authorization

Phase A would allow only the ten frozen attack/test containers to be whole-file hashed and projected by the production positive allowlist into timestamp plus approved scientific features. No label, scenario, attack-type, hidden-class, or unknown field may be row-deserialized. The exact 72-cell census must terminate with one success or method-failure receipt per cell. All successful prediction and Rule-trace bytes must be reopened and replayed before the global state can become `GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED`.

Phase B would remain technically locked until the complete global freeze is replayed under the same executable manifest. One opaque, single-issue, single-consume lease would permit the fresh-process custodian to read only approved official label/scenario sources and write method-blind scenario and denominator authorities. It cannot receive or read prediction artifacts. Results would then be built only from frozen coordinate-bound authorities and independently replayed.

## Panels and reporting boundary

- HAI23 test2: 38 nominal official scenarios, primary held-out panel.
- HAI22: 58 nominal official scenarios, external replication 1.
- HAI21: 50 nominal official scenarios, external replication 2.

Primary reporting remains version-separated P1-eligible Scenario Recall and frozen normal false episodes/hour. The 146 nominal scenarios are not IID and no pooled Recall is primary. A failed primary prediction cell makes the affected method/panel `NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE`; successful-file partial Recall is prohibited.

## Stop conditions

Execution must fail closed for any authority, schema, projection, dispatch, custody, hash, cell-census, timestamp, lease, scenario, denominator, result, or independent-replay mismatch. No post-result tuning, method substitution, fallback executor, attack-informed eligibility, or provider action is authorized.

Approval of this V2 brief would authorize DG-05 execution under the exact manifest above. Until that explicit approval is given, all attack/test and label/scenario access remains prohibited.
