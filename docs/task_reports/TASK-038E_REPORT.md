# TASK-038E Report

Status: `passed_four_branch_outer_comparison`

## Completion

TASK-038E registered the frozen TASK-038D selections before outer-value
access, mapped 249 logical records to 146 physical rule executions, reused 21
exact TASK-037E predictions, and executed the remaining 125 units twice in
fresh rootless Podman containers. All 146 physical predictions were
deterministic. The task then froze:

- 320 branch/variant/KPI/arm predictions;
- 76 Review parent/revision combined-prediction pairs;
- 13 repaired-rule combined predictions.

Outer labels were loaded only after this complete prediction freeze. A0
reproduced all 80 TASK-037E arm/KPI prediction hashes and metrics exactly.
No selected rule was substituted, restored, or converted to no-op.

## Branch Results

All metrics below are direct PA-free macro averages over ten KPI series.
`FP/10k` is false-positive points per 10,000 normal points.

| Variant | Branch | Arm | Precision | Recall | Point F1 | Event F1 | FP/10k |
|---|---|---|---:|---:|---:|---:|---:|
| LSTMADalpha | A0 | Detector | 0.6809 | 0.2945 | 0.3541 | 0.4379 | 24.13 |
| LSTMADalpha | A0 | D+FN | 0.6342 | 0.5117 | 0.4884 | 0.5415 | 45.52 |
| LSTMADalpha | A0 | D+FP | 0.6809 | 0.2945 | 0.3541 | 0.4379 | 24.13 |
| LSTMADalpha | A0 | Full | 0.6342 | 0.5117 | 0.4884 | 0.5415 | 45.52 |
| LSTMADalpha | A1 | Detector | 0.6809 | 0.2945 | 0.3541 | 0.4379 | 24.13 |
| LSTMADalpha | A1 | D+FN | 0.6078 | 0.5128 | 0.4544 | 0.5583 | 97.43 |
| LSTMADalpha | A1 | D+FP | 0.6809 | 0.2945 | 0.3541 | 0.4379 | 24.13 |
| LSTMADalpha | A1 | Full | 0.6078 | 0.5128 | 0.4544 | 0.5583 | 97.43 |
| LSTMADalpha | A2 | Detector | 0.6809 | 0.2945 | 0.3541 | 0.4379 | 24.13 |
| LSTMADalpha | A2 | D+FN | 0.6342 | 0.5117 | 0.4884 | 0.5415 | 45.52 |
| LSTMADalpha | A2 | D+FP | 0.7306 | 0.2932 | 0.3704 | 0.4662 | 18.50 |
| LSTMADalpha | A2 | Full | 0.6814 | 0.5104 | 0.5047 | 0.5702 | 39.89 |
| LSTMADalpha | A3 | Detector | 0.6809 | 0.2945 | 0.3541 | 0.4379 | 24.13 |
| LSTMADalpha | A3 | D+FN | 0.6078 | 0.5128 | 0.4544 | 0.5583 | 97.43 |
| LSTMADalpha | A3 | D+FP | 0.7837 | 0.2679 | 0.3553 | 0.4849 | 16.23 |
| LSTMADalpha | A3 | Full | 0.6741 | 0.5000 | 0.4666 | 0.6179 | 89.83 |
| LSTMADbeta | A0 | Detector | 0.6673 | 0.3886 | 0.4233 | 0.3518 | 33.88 |
| LSTMADbeta | A0 | D+FN | 0.6016 | 0.5820 | 0.4782 | 0.4235 | 148.40 |
| LSTMADbeta | A0 | D+FP | 0.7044 | 0.2864 | 0.3476 | 0.4187 | 24.10 |
| LSTMADbeta | A0 | Full | 0.5917 | 0.4870 | 0.3880 | 0.5002 | 142.27 |
| LSTMADbeta | A1 | Detector | 0.6673 | 0.3886 | 0.4233 | 0.3518 | 33.88 |
| LSTMADbeta | A1 | D+FN | 0.6040 | 0.5830 | 0.4796 | 0.4235 | 148.40 |
| LSTMADbeta | A1 | D+FP | 0.7044 | 0.2864 | 0.3476 | 0.4187 | 24.10 |
| LSTMADbeta | A1 | Full | 0.5940 | 0.4880 | 0.3895 | 0.5002 | 142.27 |
| LSTMADbeta | A2 | Detector | 0.6673 | 0.3886 | 0.4233 | 0.3518 | 33.88 |
| LSTMADbeta | A2 | D+FN | 0.6330 | 0.6062 | 0.5077 | 0.4246 | 148.40 |
| LSTMADbeta | A2 | D+FP | 0.7961 | 0.2694 | 0.3599 | 0.4704 | 11.08 |
| LSTMADbeta | A2 | Full | 0.6799 | 0.4965 | 0.4215 | 0.5499 | 131.92 |
| LSTMADbeta | A3 | Detector | 0.6673 | 0.3886 | 0.4233 | 0.3518 | 33.88 |
| LSTMADbeta | A3 | D+FN | 0.6323 | 0.6052 | 0.5067 | 0.4246 | 148.40 |
| LSTMADbeta | A3 | D+FP | 0.7829 | 0.2806 | 0.3659 | 0.4748 | 15.84 |
| LSTMADbeta | A3 | Full | 0.6657 | 0.5084 | 0.4245 | 0.5539 | 136.30 |

## Component Evidence

Repair recovered all 13 runtime failures in TASK-038B, but outer utility was
mixed: four repaired rules were useful relative to detector-only, four were
equal, and five were regressive. The two repaired rules selected in A1 split
one useful and one regressive outcome. Consequently, A1 Full minus A0 Full
point-F1 was `-0.0340` for Alpha and `+0.0015` for Beta.

Among 76 reviewed executable rules, A2 recorded 30 positive transfers, two
negative transfers, and two no-transfer outcomes among 35 revisions; A3
recorded 34 positive transfers, two negative transfers, two no-transfer
outcomes, and two inner-regression/outer-recovery outcomes among 41 revisions.
All 19 reviewed rules selected by TASK-038D had positive parent-relative outer
transfer. This transfer evidence does not itself establish branch superiority
because branch outcomes also depend on independent FN/FP reselection and
composition.

The 19 selected A2/A3 FP rules included four safe corrections, 14 costly
corrections, 14 harmful classifications, and one ineffective correction.
Categories can overlap. TP and true-anomaly-event removal remain reported in
the dedicated safety artifact; no harmful rule was removed after observation.

A2 Full minus A0 Full point-F1 was positive for both variants: `+0.0163` for
Alpha and `+0.0335` for Beta. A3 Full minus A0 Full was mixed:
`-0.0218` for Alpha and `+0.0364` for Beta. The complete A3 branch therefore
did not show variant-robust point-F1 direction. Paired KPI bootstrap intervals
are descriptive only and do not support population-level significance claims.

### Selected Review Survival

All 19 reviewed rules selected by TASK-038D had positive parent-relative outer
transfer. Relative to the A0 branch at the same variant/KPI/direction, 15
selected Review records had positive Full point-F1 deltas, three had negative
deltas, and one tied. Multiple selected directions in one branch/KPI share the
same Full delta.

| Branch | Variant | KPI | Dir | Reviewed hash | Dir delta vs A0 | Full delta vs A0 | Parent F1 | Reviewed F1 | Transfer delta |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| A2 | LSTMADalpha | `05f10d3a-239c-3bef-9bdc-a2feeb0037aa` | FP | `86e2537ad7ab8cb7aa1fce141001464e1f518aced010127f2deaf8e21b6b2ec5` | 0.004116 | 0.003663 | 0.315789 | 0.617450 | 0.301660 |
| A2 | LSTMADalpha | `42d6616d-c9c5-370a-a8ba-17ead74f3114` | FP | `276fa5d48dbc540c456d7b64164ece0f4732d4c5dace29fd4ecaff3076815123` | 0.001208 | 0.002220 | 0.127168 | 0.225806 | 0.098639 |
| A2 | LSTMADalpha | `43115f2a-baeb-3b01-96f7-4ea14188343c` | FP | `b47e6a37a1459110c760582cdcf6033dca65ef24046d8114ede31733beef7774` | 0.157140 | 0.157140 | 0.331551 | 0.655602 | 0.324051 |
| A2 | LSTMADalpha | `55f8b8b8-b659-38df-b3df-e4a5a8a54bc9` | FP | `db90396c6b628271ed63e20bf65d1874c1d776a544714e16f164a7cd84c603c5` | 0.000000 | 0.000000 | 0.039604 | 0.156250 | 0.116646 |
| A2 | LSTMADbeta | `05f10d3a-239c-3bef-9bdc-a2feeb0037aa` | FP | `d1b9e570325b247d050ef6f619c2445e8e63ccc819177e412e61cb59ec0f86f6` | 0.109814 | 0.003775 | 0.438596 | 0.612378 | 0.173781 |
| A2 | LSTMADbeta | `43115f2a-baeb-3b01-96f7-4ea14188343c` | FP | `16ee8e09217fb804639ad12e6fbe75616b7d4411a2393db308a69bc6fd814299` | 0.068272 | 0.065716 | 0.273224 | 0.577778 | 0.304554 |
| A2 | LSTMADbeta | `431a8542-c468-3988-a508-3afd06a218da` | FP | `5653cc3489b8310c616b8172bebef11befe8cff948200e157663cb5c9506095f` | -0.001031 | -0.002353 | 0.039758 | 0.049305 | 0.009547 |
| A2 | LSTMADbeta | `55f8b8b8-b659-38df-b3df-e4a5a8a54bc9` | FN | `8b45d6d0046f8ce6ef6c13c21267894ad9f8af14861a5c418603013dc2b88534` | 0.295354 | 0.333088 | 0.017519 | 0.437086 | 0.419567 |
| A2 | LSTMADbeta | `55f8b8b8-b659-38df-b3df-e4a5a8a54bc9` | FP | `f4d9bc1e515db0cfd6e1fa88991ae28f61f0dde0e03fad3ddc4a9de2466ce1fe` | 0.014789 | 0.333088 | 0.039604 | 0.156522 | 0.116918 |
| A2 | LSTMADbeta | `6efa3a07-4544-34a0-b921-a155bd1a05e8` | FP | `80d43118d464ca54ff9e5386e351c3e6fa63507cd8f3bae2a88bae32689287a5` | -0.068018 | -0.065420 | 0.381344 | 0.748396 | 0.367052 |
| A3 | LSTMADalpha | `05f10d3a-239c-3bef-9bdc-a2feeb0037aa` | FP | `ff330ae08db7634444a36d78c0402c8d7c0b315588c6b764eab65cb2dcaaac4d` | -0.061333 | 0.044358 | 0.315789 | 0.552000 | 0.236211 |
| A3 | LSTMADalpha | `42d6616d-c9c5-370a-a8ba-17ead74f3114` | FP | `8d43b204a42d58be4ab552b4994bf536ad620e40b4cfd30efb4efe760cf1b615` | -0.006020 | 0.006722 | 0.127168 | 0.218579 | 0.091412 |
| A3 | LSTMADalpha | `43115f2a-baeb-3b01-96f7-4ea14188343c` | FP | `97f29df0b50af95d09efce66893eb814ceeb1c73951d98bb09cc7a0bc23dbd66` | 0.063750 | 0.063750 | 0.085890 | 0.562212 | 0.476322 |
| A3 | LSTMADalpha | `55f8b8b8-b659-38df-b3df-e4a5a8a54bc9` | FP | `170e301403e6d06e0721179fe90689d4afa1edce6a1d316f60bde8a6c5d96154` | 0.014690 | 0.007234 | 0.039604 | 0.170940 | 0.131336 |
| A3 | LSTMADbeta | `05f10d3a-239c-3bef-9bdc-a2feeb0037aa` | FP | `0fdc6c84521b3bda7f32987ac0090a26e7e6023e614da7bb687c6169a0c9c321` | 0.129380 | 0.004487 | 0.309179 | 0.631944 | 0.322766 |
| A3 | LSTMADbeta | `43115f2a-baeb-3b01-96f7-4ea14188343c` | FP | `51e84e52372041e8d287fded54db91aca4a24483c27c4799912982f4e7483321` | 0.061923 | 0.061923 | 0.153846 | 0.571429 | 0.417582 |
| A3 | LSTMADbeta | `431a8542-c468-3988-a508-3afd06a218da` | FP | `28f34adda38322a327436715ce5be76748a795a04eee745611601e53f2502386` | -0.002430 | -0.003181 | 0.039758 | 0.047906 | 0.008148 |
| A3 | LSTMADbeta | `55f8b8b8-b659-38df-b3df-e4a5a8a54bc9` | FN | `dee584247c33aca47d7629962141b650cc2b83ff496cc86e8f615bc7e367ba66` | 0.284934 | 0.301125 | 0.017519 | 0.426667 | 0.409147 |
| A3 | LSTMADbeta | `55f8b8b8-b659-38df-b3df-e4a5a8a54bc9` | FP | `001d9a647d86fc4de54ba36544f7ac9a4a47e05ab41342618043ea193c5e71b2` | -0.004980 | 0.301125 | 0.000000 | 0.136752 | 0.136752 |

## Cost

The study inherited 13 Repair calls and 77 Review calls, for 90 unique agent
calls and 404,399 provider-reported tokens. Shared Repair calls were counted
once. Monetary cost was not computed because no pricing artifact was frozen
before execution.

## Boundary

The TASK-038E outer partition is a previously exposed follow-up validation
partition. Repair and Review used generation or inner data only, and A0-A3
selections were frozen on inner before TASK-038E outer execution. However,
the broader research program and agent experiment were designed after earlier
inspection of this outer partition. The results are descriptive evidence and
do not support an untouched confirmatory superiority claim.

TASK-038E executed the one-way, previously exposed outer-validation comparison
of the frozen A0 one-shot, A1 Repair-only, A2 Review-only, and A3
Repair-plus-Review branches. The TASK-038D selections were used without
modification. An exact logical and physical execution registry was committed
before outer-value access, identical physical rule executions were
deduplicated, and every new rule prediction was replayed twice in fresh
rootless containers. Detector-only, detector-plus-FN, detector-plus-FP, and
FP-then-FN Full Aggregator predictions for all branches were frozen before
outer labels were loaded. A0 was required to reproduce TASK-037E exactly.
The task additionally evaluated all reviewed executable rules against their
exact parents for outer transfer and all repaired executable rules for outer
detector-combined utility. It reports directional benefits and costs,
true-positive removal by FP correction, inner-to-outer generalization gaps,
LSTMAD variant consistency, provider usage, and paired descriptive
uncertainty. No provider or agent call, detector retraining, threshold
reselection, outer-based selection, or sealed-test access occurred. Because
the outer partition was previously exposed, these results are descriptive
component evidence and do not establish final ARGOS superiority.
