# DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access

Status: `USER_DECISION_REQUIRED`

No attack/test payload, label value, scenario interval, scenario target, or real eligibility was accessed while preparing this gate.

## Scope and phases

One conditional approval covers exactly HAI23 test2 (38 nominal scenarios), HAI22 (58), and HAI21 (50). Phase A permits strict positive-allowlist feature projection and all frozen-method predictions in the fixed HAI23 → HAI22 → HAI21 order. Phase B can issue exactly one opaque label/scenario lease only after the V2 exact cell census, prediction-artifact replay, append-only state chain, and durable `GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED` manifest all pass.

## Frozen authorities

- method bundle: `dab320da47489e5093862b7c4675523c3e6b710faceb753e7f39c8e56f002fe2`
- metric V2: `6b8177f83251bb18b5953782697db962adf240bd3ac23e4dd4a8055cc714a084`
- P1 custodian V2: `7df085fb00deab3c2aa6bc22988cdea908847893fdbba910296e1c908ac1f125`
- global custody V2: `957c79d331a721eb0f04381abfdecb797d1f9f7814d2e953a93a91d3ca241879`
- preregistration V2: `923e72b5aef82cf77eb24c5525c014d9ac848c701716ab824736a556a7c8bbe2`
- eTaPR conformance V2: `d8cfcea5cc64f927e58871437b3a33f99e17299de32935f02407569add7600e2`
- statistical analysis V2: `cf90fee47e9294873e09aa516df8163328ee924d756c66b18a811c4ea2f9b463`
- attack feature allowlists: `1ec98999df85eb9d8501439437dde7412a5188d3a40ce5f27a7beb08c2a1729f`
- exact public attack-file census: `5018ba8d01e32a8a2ff4cf95cdb6ca75b51b006b812acf5cffe2b1d26b8a6a16`
- P1 mapping authorities: `74f15b4b7cf22972ecbeb46b7133736f93bf58af74a439b5f5cfb9de993596b5`
- Fusion: `587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc`
- HAI23 detector private binding: `abe9b3abfdf792b247492d7cc9e195c7f54ece57fd7b9337d38e04efd7241780`
- HAI23 PCA fit/threshold: `f1f29e8a51f2c3fd81654b2b11ab86c3208446db8effdb9e86902bb9fc2ca530` / `58d38959d47b3dced9a450bfd8bde9af1dcb8fab0a013e4145c4a657ff4d284b`
- HAI23 IF fit/threshold: `425533c995a71b6c8dd7bd20ada3c4c060a3c6e2d5859268271bcfd6f3f44780` / `4f143fed3914593b31db7ba8d93ad08ec241307b2d091675e0d0f757603daa5d`
- HAI22 detector: `3abe6aeb898e8ea0bbca9eb41bab968d6a53232aee3c70a3fc5885008ffe67c4`
- HAI21 detector: `0eb58f17096d5ca0d5bbbc4c9d51a7220dc45d19830e00671a0fbfaee78315d6`
- current panel/task indexes: `PANEL_REGISTRY_V4.csv` / `IMPLEMENTATION_TASK_INDEX_V4.csv`

## Non-negotiable execution

Every exact panel × physical file × primary/secondary method cell terminates with either a success receipt bound to replayed prediction bytes or a distinct method-failure receipt that contains no invented prediction/alarm fields. Phase A binds each public file identity to raw-container/header/official-source hashes in a typed physical-file authority before projection. Labels stay locked until projection and prediction artifacts plus the complete manifest are durably replayed. The lease is append-only, single-issue, single-consume, and remains consumed if the reader fails. After lease issue, prediction artifacts, models, portfolios, thresholds, Fusion, mappings, and eligibility logic are immutable.

Official Scenario Recall is computed from same-version, same-file overlap against independently eligible official closed intervals. Paired tables require exact dataset/file/scenario identities plus identical scenario and eligibility authority hashes. Per-file eTaPR outputs are retained alongside the canonical disjoint union. Cross-version primary pooling and point adjustment are prohibited.

No provider call, GDN training, method redesign, attack access before approval, post-result tuning, or professor submission is authorized.
