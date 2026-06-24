"""Data contracts, manifests, and leakage-safe split utilities."""

from paperworks.data.contracts import (
    DataViewManifest,
    DataViewName,
    DatasetFile,
    DatasetManifest,
    SplitManifest,
    SplitRole,
)
from paperworks.data.files import (
    CsvMetadata,
    inspect_csv_metadata,
    resolve_data_root,
    sha256_file,
    validate_local_files,
)
from paperworks.data.splits import (
    WindowSpec,
    assert_no_overlapping_ranges,
    assert_split_permitted,
    build_data_view_manifest,
    build_sequential_split_manifests,
    generate_split_windows,
    required_purge_gap,
)

__all__ = [
    "CsvMetadata",
    "DataViewManifest",
    "DataViewName",
    "DatasetFile",
    "DatasetManifest",
    "SplitManifest",
    "SplitRole",
    "WindowSpec",
    "assert_no_overlapping_ranges",
    "assert_split_permitted",
    "build_data_view_manifest",
    "build_sequential_split_manifests",
    "generate_split_windows",
    "inspect_csv_metadata",
    "required_purge_gap",
    "resolve_data_root",
    "sha256_file",
    "validate_local_files",
]

