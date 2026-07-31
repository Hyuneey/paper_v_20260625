# V6 Detector Error Context

`DetectorErrorContextV1` is an optional reference-only artifact for authorized
development diagnostics or inner utility assessment. It may identify false
negative or false positive direction and bind detector artifacts, prediction
references, event references, and bounded context-window references.

Allowed split-role and purpose pairs are:

| Split role | Purpose |
|---|---|
| `development` | `development_diagnostic` |
| `inner_utility` | `inner_utility_assessment` |

All other roles fail closed. Outer and sealed use are prohibited.

False-positive context is always `supplementary_only=true` and cannot be the
primary correction direction. False-negative context may be marked primary.

The context contains references only. It cannot contain raw values, labels,
prediction arrays, timestamps, or rows. It cannot replace normal relation
evidence or grant validity/runtime authority.
