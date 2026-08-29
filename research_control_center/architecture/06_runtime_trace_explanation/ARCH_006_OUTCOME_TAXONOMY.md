# Frozen D1 outcome taxonomy

| Outcome | Exact condition | Alarm? | Trace evidence | Scientific meaning | System-error distinction |
|---|---|---:|---|---|---|
| `evaluated_expected_response` | retained isolated source event exists and the 3-row target response median crosses the normal target-noise authority in the confirmed direction | no | task-specific result record and trace hash | this frozen rule opportunity was satisfied | authority/custody failures never enter this state |
| `evaluated_anomaly` | retained isolated source event exists but the response does not cross the strict expected-direction boundary | yes | task-specific result record and trace hash | this relation opportunity was violated under the frozen executable contract | this is not an attack label, causal diagnosis, or episode |
| `abstain` | a formed opportunity lacks complete source or target context | no | final state plus trace hash; the public prediction does not retain the abstention reason | the runtime did not produce a relation judgment | malformed authority, replay mismatch, or non-finite input is an error, not abstention |
| system error | authority, custody, source-event replay, target-state replay, schema, or factory check fails | none | exception and nonzero error path | execution is invalid and fails closed | never silently normalized into an outcome |

`PASS` and `FAIL` are explanatory shorthand only. In the frozen code, PASS corresponds to `evaluated_expected_response` and FAIL corresponds to `evaluated_anomaly`.

There is no independent configurable target-persistence test. The target evidence is a fixed three-second response window summarized by its median. Source persistence is represented by the five-row post-window stability fraction.
