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

## TASK-039B Result

Local deterministic extraction used `pypdf` 6.10.0 on the verified 50-page
manual. P1 had 36 reviewed records among 37 features; P3 had 7 of 7. P1's only
nonconstant binary field lacked an exact manual binding and remained
unresolved. All manual-backed P1 discrete controls were constant in the
authorized periods, while P3 manual-backed commands were continuous. The
policy therefore produced zero eligible sources for both processes.
