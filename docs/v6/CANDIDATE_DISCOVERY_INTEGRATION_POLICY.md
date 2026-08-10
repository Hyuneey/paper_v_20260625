# Candidate Discovery Integration Policy

`TASK-039C-INTEGRATE` forms the set union of META top 20, STAT top 20, and GDN
top 20 only when GDN passes. Pairs are de-duplicated solely by source and
target identity.

Every integrated pair retains all origin arms, rank within each arm,
method-specific evidence references, and the common-universe reference. No
cross-method numerical score is normalized, weighted, or combined. The union
is not ranked across methods in TASK-039C.

Arm usefulness is deferred to TASK-039D under an independently frozen normal
relation profiling protocol. Planning dimensions include confirmed-relation
yield and source/target coverage at 20, transfer, shortfall, and overlap. BR2
confirmed relations are not ground truth for those measurements.
