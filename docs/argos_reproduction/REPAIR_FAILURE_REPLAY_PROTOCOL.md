# Repair Failure Replay Protocol

TASK-038B replays every one of the thirteen frozen TASK-037D static-valid
runtime failures before creating a provider request.

Each relevant failing fixture is executed twice in fresh containers using the
unchanged TASK-037D image and rootless Podman controls. Only the initial rule,
one generation value-only array, and a private output directory are mounted.
Labels, detector predictions, metrics, inner data, outer data, sealed-test
data, credentials, and the repository root are absent.

A failure is reproducible only when both runs fail with the same sanitized
category and error hash while the rule, frozen chunk, and values-only input
hashes match lineage. A non-reproducible failure remains in the primary
thirteen-rule denominator but creates no Repair call.

Tracked replay records contain identifiers, hashes, categories, and booleans
only. Raw values, source, stack traces, container IDs, and local paths remain
private.
