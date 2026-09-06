# DEC-031 binding implementation

Status: `APPROVED_PREACCESS_BINDING_ONLY`

DEC-031 freezes `HIT_INTERVAL_LOCAL_DELAY`, `FAIL_FILE_ON_DUPLICATE_TIMESTAMP`, `FAIL_FILE_ON_NON_UNIT_GAP`, `FOUR_WAY_RUNTIME_IDENTITY_CENSUS`, and `NORMAL_SOURCE_DISCOVERY_THEN_SCOPED_MATERIALIZATION_IF_ABSENT`.

The primary scenario remains one official scenario with one primary HIT at most. A HIT may occur in any of its one or more closed physical-time intervals. Delay is measured from the start of the interval containing the chronologically earliest HIT. Overlap ties use earliest interval start, then canonical interval authority order. Interval endpoints need not be sampled rows.

Every scientific file must first establish a unique, strictly increasing, exact `+1 second` physical timestamp authority. Duplicate or non-unit timelines are terminal file failures; no row is removed, inserted, averaged, interpolated, or bridged. Prediction is not invoked for the invalid file, and primary partial-file effectiveness metrics remain prohibited.

Runtime reporting distinguishes configured, formed, evaluated, and alarming Rule identities. `SYSTEM_ERROR` stays separate from PASS, FAIL, and ABSTAIN. Alarm episodes are derived from the per-file union of immutable Rule FAIL timestamps after timeline validation; Rule multiplicity at one physical second does not inflate the count. Missing trace evidence is an error, never measured zero.

Normal-source authorization is prospective and narrow. Existing private sources must be discovered and replayed first. Materialization is permitted only for absent required source evidence, using exact frozen normal projections, fitted detector objects, Rule portfolios, numeric/Formal V4 authorities, and Fusion. No fit, calibration, threshold, Rule, policy, split, or method selection may change. Excluded normal label values remain unparsed and unused.

This decision does not authorize real attack/test, label/scenario, provider, credential, training, refit, or DG-05 execution. A new exact executable release and separate user reapproval remain required.
