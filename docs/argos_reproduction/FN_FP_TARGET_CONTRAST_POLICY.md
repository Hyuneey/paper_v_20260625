# FN/FP Target and Contrast Policy

## FN

The target chunk must intersect a frozen generation FN segment and contain at
least one anomaly point missed by the detector. The contrast is an aligned,
full-length chunk in which every point is both ground-truth normal and
detector-predicted normal.

The intended future binary composition is:

```text
max(detector, FN rule)
```

## FP

The target chunk must intersect a frozen generation FP segment and contain no
ground-truth anomaly point. The contrast is an aligned chunk containing at
least one detector true-positive anomaly.

The intended future binary composition is:

```text
min(detector, FP rule)
```

## Matching

For every target, candidate contrast chunks are summarized by value mean and
sample standard deviation. The two dimensions are standardized using the
eligible contrast pool, ranked by Euclidean distance to the target summary,
and tied by earliest start. Target overlap is prohibited.

This is a deterministic project-owned reconstruction. The ARGOS paper
describes random one-for-one examples, while the pinned implementation also
contains iteration-based and closest-chunk behavior. No claim is made that the
matching policy is the exact paper experiment.
