# ARCH-001 Label Access Timeline

Scientific authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

This is a static control-flow audit. It did not open HAI payloads or execute a scientific path.

## Normal construction path

`train1/train2 features` **LABEL-BLIND** → candidate discovery / relation fit / normal-only numeric authority → evidence pack → T0/T1/T1-B/T2 → deterministic verifier → COMMON-42.

The normal train files are represented with label availability `unavailable`. Construction modules also carry task-specific prohibitions on test files, labels, attack summaries, and backward use of BR2 pair outcomes. Evidence materialization consumes already frozen ledgers and does not reread train or test payloads.

## D0 INNER

`train1/train2 features` → preprocessing and PCA fit → `train3 features` → SPE threshold calibration → `train4 features` → normal sanity → `test1 features` → label-blind DetectorPrediction → **durable atomic write and byte replay** → state `PREDICTION_FROZEN` → `label-test1` hash/parse → metrics → unchanged prediction-byte check.

Label state: **FORBIDDEN** before the persistent freeze; **LABEL-ACCESSIBLE** only after the state transition.

## D1 INNER

COMMON-42 + private normal-only numeric authorities + `test1 features` → full rule census → label-blind `ScientificRulePredictionArtifactV1` object → object self-hash/factory custody validation → `label-test1` hash/parse → metrics → public reports, including the RulePrediction file.

Label state: the prediction content is computed and self-hashed before labels, and the label loader requires that issued object. However, the production controller does not durably persist and reopen the public RulePrediction file before label access. The file is written later by `_public_reports_v1`. Therefore:

- label blindness of the decision object: **VERIFIED**;
- construction-before-label ordering: **VERIFIED**;
- durable prediction-file-before-label ordering: **NOT VERIFIED / IMPLEMENTATION GAP**.

This gap does not establish that labels changed rules or alarms. It weakens crash/replay evidence for the ordering claim and must be remediated only in a separately authorized future task; the frozen D1 result is not modified here.

## D2 V1 INNER

Frozen D0 prediction + frozen D1 prediction + frozen source map → label-blind fusion → CombinedPrediction atomic write/reopen → state `COMBINED_PREDICTION_FROZEN` → `label-test1` hash/parse → metrics → input and combined bytes rechecked.

D2 V1 design declared `test1_used_for_design=false` and `labels_used_for_design=false`. Fusion execution itself reads no test1 feature file.

## D2 V2 INNER

Frozen D0/D1 predictions + source map + normal-derived native horizons → label-blind V2 fusion → CombinedPredictionV2 atomic write/reopen → frozen state → `label-test1` parse → metrics → byte rechecks.

The V2 policy was explicitly designed after and informed by prior INNER outcomes. The design task itself did not reopen label or feature files, and its fusion does not consume labels, but it is an **INNER-development, label-informed policy**, not independent confirmation.

## OUTER / test2

The intended state machine is: one-shot grant → private authority validation → test2 feature custody → all three predictions durably frozen → separate test2 label authority → metrics. The recovery attempt reached the first test2 feature custody check and rejected the file before reading bytes.

- feature file custody access attempts: `1` in the historical recovery record;
- feature bytes read: `0`;
- feature hashes/semantic parses: `0`;
- label file accesses/bytes/parses: `0`;
- predictions/metrics: `0`;
- scientific outcome: **unavailable**.

“Test2 untouched” is too imprecise for history. The accurate statement is that no test2 payload byte or semantic content was read, although one custody-level file access was attempted and rejected.

## Overall finding

No verified label-to-fit or label-to-rule backward path was found. D0 and D2 enforce durable prediction-before-label ordering. D1 enforces label-blind object construction before labels but lacks the equivalent durable-file gate. Test1 has development/pilot reuse in D2 V2 design, which limits independence but is not concealed as held-out validation.
