# D0 preservation

Both policies implement pointwise preservation:

```text
D2_alarm(t) = D0_alarm(t) OR policy_admits_D1(t)
```

V1 `fuse_point_v1` and V2 `_fuse_point_v1` return an alarm whenever D0 is true.
The builders additionally reject a record if `d0_alarm and not d2_alarm`.
Therefore no frozen D0 point is removed or moved by fusion. Episode grouping is
a later label-aware metric operation and is not the preservation unit.

Classification: **VERIFIED_POINTWISE**.
