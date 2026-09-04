# Required prospective event-evidence binding

Status: **USER_SCIENTIFIC_DECISION_REQUIRED**.
Stop code: `BLOCKED_GDN_METHOD_CHANGE_REQUIRED`.
Affected versions: HAI22 and HAI21. No result was computed to choose an option.

## Exact inconsistency

The task requires unchanged EXP-01C event-definition semantics, split-pure
provider evidence, and the frozen EXP-03B aggregation/projection semantics.
The existing implementations do not define one estimator meeting all three:

1. `scripts/run_exp01c_gdn_hai.py::_reference_and_numeric` builds events from
   train3-confirmed directional identities and horizons, the final EXP-02
   selected policy, max-pooled train1/train2 numeric roles, and train4 values.
   `evaluate_exp01c_checkpoint_v1` conditions target/horizon masking losses on
   those event indices.
2. `exp03b_gdn_v1.infer` instead evaluates all precommitted same-split purged
   validation windows. Its EdgeMask is **global**, not event-conditioned.
3. EXP-03B exposes five GDN rows, one per horizon, without a source-direction
   axis. Its median-of-available-seed signed effect rule does not define how
   two event-direction effects become one horizon row.

Copying (1) would violate the new provider firewall. Calling (2)
event-conditioned would mislabel the method. Selecting new event thresholds
or reducing direction-conditioned evidence implicitly would change scientific
evidence rather than merely adapt node count or file identity.

## Minimal binding to approve before scientific execution

Freeze all of the following together:

- Event amplitudes/stability: existing SCI-01 common fixed split-local source
  event parameters, or locked-policy split-local parameters. These produce
  different event populations; neither is uniquely inherited from both paths.
- Evaluation support: all same-split windows, or event indices intersected with
  each seed's precommitted purged validation windows. The latter preserves the
  historical EXP-03B evaluation support.
- Direction/horizon representation: preserve both directions and five horizons
  in ten event rows, or explicitly define a direction-pooling estimator. Do
  not silently collapse direction-specific losses into the historical five rows.
- Zero event / edge absent: explicit unavailable state, not a fabricated zero;
  specify eligible seed contributions and retain signed effects. The historical
  global effect uses the median of available graph-member seed effects.

Suggested prospective amendment, **not implemented or approved here**: SCI-01
split-local events, per-seed purged-validation intersection, ten direction ×
horizon event rows alongside separately labeled five global rows, unavailable
events/edges excluded from the effect median with availability counts. This
needs an explicit scientific approval and new prompt/retrieval schema freeze.

The requested train2 STAT/GDN retrieval also needs a prospective closed schema:
historical EXP-03B repair retrieval is structural-only. Adding these requested
fields is authorized in principle but does not resolve the estimator above.

## Scope retained

Context mapping, positive-allowlist projection, variable-node synthetic QA,
parent preservation and metric review continue. Scientific training and T0
execution wait for the complete required train1 evidence contract; no partial
checkpoint set or empirical proxy is created. Candidate unions, SCI-01 gates,
T0 logic, SCI-02B, Formal V4 and guard semantics are unchanged. GDN never becomes
a candidate or verifier admission gate.

The exact 12-run matrix remains HAI22/HAI21 × TRAIN1_ONLY/TRAIN2_ONLY ×
11/23/37, one GPU owner. It is not executed. Provider budget is not ready;
only `3 × 29 = 87` calls/version is structurally derivable. No exact tokens or
cost may be invented before evidence and requests exist.
