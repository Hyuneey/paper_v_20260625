# HAI P1/P3 Metadata Audit

TASK-039B uses the official technical manual as the primary metadata source,
followed by official graph references, reviewed tag patterns, and normal-data
domain diagnostics. Domain behavior can confirm whether a value is binary,
discrete, continuous, or constant. It cannot invent a physical role.

Every public `HAIVariableMetadataV2` record binds a P1 or P3 tag to manual
pages, a bounded description, optional official graph references, a reviewed
semantic role, an observed domain, eligibility flags, exclusions, and a
self-hash. Unresolved variables are retained and are never eligible.

Eligible sources are reviewed binary/discrete controls, actuator states, or
actuator feedback. Eligible targets are reviewed, nonconstant continuous
process sensors. Setpoints, alarms, derived fields, constants, unknown roles,
P2/P4 signals, and continuous actuator commands are excluded from the first
MVP.

No full manual text, raw values, timestamps, or test/attack information is
stored in the metadata registry.
