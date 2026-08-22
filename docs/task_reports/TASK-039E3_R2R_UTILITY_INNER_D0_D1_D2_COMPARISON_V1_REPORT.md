# INNER D0/D1/D2 Scientific Comparison V1

## Experimental arms

D0 detector-only, D1 verified-rule-only, and D2 detector plus frozen corroborated rule recovery are compared from integrity-audited frozen predictions.

## Frozen evaluation protocol

Fourteen strict label-one attack events and 51,019 normal seconds are evaluated with maximal contiguous alarm episodes. No arm was executed or changed.

## Primary comparison table

| Arm | Detected attacks | Recall | Normal false episodes | FAR/hour |
|---|---:|---:|---:|---:|
| D0 | 11 | 0.7857142857142857 | 7 | 0.4939336325682589 |
| D1 | 13 | 0.9285714285714286 | 574 | 40.50255787059723 |
| D2 | 11 | 0.7857142857142857 | 10 | 0.7056194750975128 |

## Attack-event overlap comparison

D0 and D1 jointly detect 10 events; D0-only 1; D1-only 3; neither 0. Coordinates remain private.

## D0-miss recovery potential

D0 misses three events. D1 detects 3 of them, giving potential recovery rate 1.0.

## D2 realized recovery

D2 recovers 0 D0-missed events; realized recovery and retention are 0.0 and 0.0.

## False-alarm tradeoff

D2 adds 3 normal false-alarm episodes and 0.21168584252925388 FAR/hour over D0.

## What D1 demonstrates

D1 supplies high-sensitivity, high-false-alarm rule signal; it is not established as operationally superior.

## What D2 V1 demonstrates

D2 V1 shows no INNER recall gain and positive additional false-alarm cost. Current combined utility is unsupported on INNER.

## What cannot yet be concluded

No causal gate-failure mechanism or alternative fusion policy is established.

## Thesis implications

Rule-layer sensitivity evidence is supported; D1 operational false-alarm limitation is supported; D2 V1 incremental recovery is unsupported. This does not invalidate rule construction.

## Why OUTER remains sealed

OUTER is held pending an INNER D2 failure diagnostic; test2 remains untouched.

## Exact next diagnostic question

Why did D1 alarms capable of detecting D0-missed events fail exact same-second two-distinct-source corroboration?

<!-- BEGIN INNER D0 D1 D2 COMPARISON REPORT PROVENANCE V1 -->
Report-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1
Report-Self-Hash: 86d8c1ee67e75461fab51fb43242f0532014e9c5585c5fab55a9da05c970966b
Bundle-Hash: 168a3566f6e8310168a8c282c6927d2d992dbd674235952bb9b1aa9a79ff5469
Receipt-Hash: d444ed1f7979270b945c03f2656b92e8ef7ebf8e98eca2f88f976999da00216e
<!-- END INNER D0 D1 D2 COMPARISON REPORT PROVENANCE V1 -->
