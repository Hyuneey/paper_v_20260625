# Explanation Provenance Contract

## Trace chain

Every explanation must resolve to:

```text
accepted rule
-> verifier result
-> runtime satisfaction trace
-> graph edge
-> anomaly-anchored evidence package
-> matched normal reference
-> approved parameter records
-> detector/fusion conflict record when applicable
```

`schemas/explanation_record_schema.json` records these references plus interval,
subsystem, variables, relation, expected/observed behavior, violation type,
lag, detector/rule/fusion results, renderer version, and optional natural text.

## Renderer limits

The renderer may paraphrase verified facts. It cannot introduce a variable,
threshold, event, graph edge, detector result, causal direction, root cause, or
physical conclusion absent from the trace chain.

Required flags state that no causal or root-cause claim was made. A renderer
violation rejects the explanation artifact but does not change the underlying
accepted rule or runtime result.

## Machine-readable priority

The structured record is authoritative. Natural-language text is optional and
must be regenerable from the same references. Explanation quality is evaluated
separately from anomaly detection performance.
