# V6 Dataset Manifest V2

## Purpose

The v2 data contracts describe local research datasets without assuming a
particular dataset, one global label column, one process, or one file layout.
They are additive contracts under `paperworks.data`; existing v1 classes retain
their historical behavior.

## Dataset Files

`DatasetFileV2` records:

- logical file role and safe POSIX-relative local path;
- SHA-256, byte size, optional row count, and compression;
- optional time range and process IDs;
- optional per-file label availability;
- provenance status.

Label availability is file-specific. A manifest may therefore contain normal
files without labels and evaluation files with labels without inventing a
shared label contract.

## Dataset Manifest

`DatasetManifestV2` binds:

- dataset identity, version or edition, source, terms, and citation;
- a mandatory local-only storage declaration;
- file records;
- optional feature count and feature-name hash;
- typed timestamp and optional label specifications;
- optional nominal sampling interval and available process IDs;
- metadata artifact references;
- provenance and creation metadata.

Unknown values remain explicit as `null`, `unknown`, or `unverified`. The
contract does not infer editions, process IDs, labels, timestamps, or
compression.

The manifest ID is a deterministic SHA-256 over canonical JSON excluding the
top-level self-hash field. Deserialization verifies any supplied self-hash.

## Data Views

`DataViewManifestV2` supports:

- canonical rule views;
- candidate-learning views;
- GDN views.

Each view binds its source dataset manifest, explicit or unknown process scope,
sampling interval, preprocessing, aggregation description, feature order,
provenance, and creation metadata.

Downsampling must be explicit. A downsampled view, or a view whose source
sampling interval is unknown, cannot be authorized for second-level rule
parameter calibration.

## Split Manifest

`SplitManifestV2` binds one dataset manifest, one view, one v6 role, ordered
non-overlapping raw ranges, optional event IDs, purge declaration, process
scope, seed, creation policy, provenance, and sealed status.

`split_before_windowing` is required to be true. Window generation never
constructs a window across a raw-range boundary.

## Non-Claims

These contracts do not establish that any local dataset is present, official,
complete, correctly typed, feasible, or approved for evaluation.
