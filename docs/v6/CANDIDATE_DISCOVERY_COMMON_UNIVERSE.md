# Candidate Discovery Common Universe

TASK-039C uses one directed P1 identity universe for all discovery arms. The
source and target lists are bound to the reviewed BR2 metadata lineage, not
rediscovered from values or names.

The source set contains 12 reviewed `control_command`, `actuator_state`, or
`actuator_feedback` variables with valid BR2 fit-only source support. The
target set contains 12 reviewed `process_sensor` variables. The sets do not
overlap, producing 144 lexicographically ordered source-target identities.

Each candidate is `(source_variable, target_variable)` for process P1 and
relation family `continuous_step_delayed_response_v1`. An arm cannot add a
variable, reverse semantic direction, or emit an out-of-universe pair.

Frozen hashes:

- Source identities: `0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234`
- Target identities: `063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7`
- Pair universe: `fc072d3e18ce4623972c2cb64f6266727092ecae03fdb0f0dd929d705e1d8557`

The primary budget is top 20. Top 10 and top 40 are prefixes of the same
deterministic arm ranking. Unsupported candidates are not used as padding.
