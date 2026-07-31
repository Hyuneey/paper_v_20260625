"""Synthetic-only factories for TASK-039P1A tests."""

from __future__ import annotations

from paperworks.data.contracts import (
    DataViewManifest,
    DataViewName,
    DatasetFile,
    DatasetManifest,
    SplitManifest,
    SplitRole,
)
from paperworks.data.contracts_v2 import (
    AggregationDescriptionV2,
    CompressionTypeV2,
    CreationMetadataV2,
    DataViewKindV2,
    DataViewManifestV2,
    DatasetFileV2,
    DatasetManifestV2,
    LabelAvailabilityV2,
    LabelSpecificationV2,
    ProvenanceStatusV2,
    RawRangeV2,
    SealedAccessStatusV2,
    SplitManifestV2,
    SplitRoleV2,
    TimestampSpecificationV2,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def creation_metadata() -> CreationMetadataV2:
    return CreationMetadataV2(
        created_at="2026-07-31T00:00:00+09:00",
        created_by="synthetic_task039p1a_test",
        code_commit="1c8a7f4",
        config_hash=HASH_D,
    )


def dataset_manifest_v2() -> DatasetManifestV2:
    return DatasetManifestV2(
        dataset_name="SyntheticCPS",
        dataset_version_or_edition="unverified",
        source_kind="synthetic_fixture",
        source_reference="tracked synthetic test",
        license_or_terms_reference="not_applicable",
        citation_reference="not_applicable",
        local_only_storage=True,
        files=(
            DatasetFileV2(
                logical_file_role="normal_measurements",
                relative_local_path="process/normal.csv",
                sha256=HASH_A,
                byte_size=100,
                row_count=10,
                compression=CompressionTypeV2.NONE,
                time_range=None,
                process_ids=("process_a", "process_b"),
                label_availability=LabelAvailabilityV2.UNAVAILABLE,
                provenance_status=ProvenanceStatusV2.VERIFIED,
            ),
            DatasetFileV2(
                logical_file_role="labeled_evaluation",
                relative_local_path="process/labeled.csv.gz",
                sha256=HASH_B,
                byte_size=None,
                row_count=None,
                compression=CompressionTypeV2.GZIP,
                time_range=None,
                process_ids=None,
                label_availability=LabelAvailabilityV2.AVAILABLE,
                provenance_status=ProvenanceStatusV2.UNVERIFIED,
            ),
        ),
        feature_count=4,
        feature_names_hash=HASH_C,
        timestamp_specification=TimestampSpecificationV2(
            field_name="timestamp",
            format="ISO-8601",
            timezone="UTC",
            provenance_status=ProvenanceStatusV2.VERIFIED,
        ),
        nominal_sampling_interval_seconds=1.0,
        label_specification=LabelSpecificationV2(
            field_name="state",
            encoding={"normal": 0, "anomaly": 1},
            provenance_status=ProvenanceStatusV2.UNVERIFIED,
        ),
        available_process_ids=("process_a", "process_b"),
        metadata_artifact_references=("metadata-synthetic-v1",),
        provenance_status=ProvenanceStatusV2.UNVERIFIED,
        creation_metadata=creation_metadata(),
    )


def data_view_manifest_v2(
    *, process_scope: tuple[str, ...] | None = None
) -> DataViewManifestV2:
    dataset = dataset_manifest_v2()
    return DataViewManifestV2(
        view_kind=DataViewKindV2.CANONICAL_RULE,
        source_dataset_manifest_id=dataset.manifest_id,
        process_scope=process_scope,
        sampling_interval_seconds=1.0,
        preprocessing_config={"scaling": "none", "missing": "reject"},
        aggregation=AggregationDescriptionV2(
            method="identity",
            source_sampling_interval_seconds=1.0,
            output_sampling_interval_seconds=1.0,
            explicit=True,
            description="No aggregation in the synthetic canonical view.",
        ),
        feature_order_hash=HASH_C,
        second_level_rule_calibration_allowed=True,
        provenance_status=ProvenanceStatusV2.VERIFIED,
        creation_metadata=creation_metadata(),
    )


def split_manifest_v2(
    role: SplitRoleV2,
    *,
    ranges: tuple[RawRangeV2, ...] = (RawRangeV2(0, 30),),
    purge_gap_samples: int = 5,
    sealed_approved: bool = False,
) -> SplitManifestV2:
    dataset = dataset_manifest_v2()
    view = data_view_manifest_v2(process_scope=("process_a",))
    return SplitManifestV2(
        dataset_manifest_id=dataset.manifest_id,
        data_view_id=view.view_id,
        role=role,
        raw_ranges=ranges,
        event_ids=None,
        purge_gap_samples=purge_gap_samples,
        process_scope=("process_a",),
        seed=7,
        creation_policy="synthetic_split_before_windowing",
        provenance_status=ProvenanceStatusV2.VERIFIED,
        sealed_access_status=(
            SealedAccessStatusV2.APPROVED
            if role is SplitRoleV2.SEALED_EVALUATION and sealed_approved
            else (
                SealedAccessStatusV2.APPROVAL_REQUIRED
                if role is SplitRoleV2.SEALED_EVALUATION
                else SealedAccessStatusV2.NOT_APPLICABLE
            )
        ),
        split_before_windowing=True,
        creation_metadata=creation_metadata(),
    )


def legacy_dataset_manifest() -> DatasetManifest:
    return DatasetManifest(
        dataset_name="SyntheticLegacy",
        source_kind="synthetic_fixture",
        source_reference="tracked synthetic test",
        dataset_edition="unverified",
        normal_data_version="unverified",
        file_fingerprints={"legacy.csv": HASH_A},
        feature_count=3,
        feature_names_hash=HASH_B,
        timestamp_column="timestamp",
        sampling_period_seconds=1.0,
        label_column="state",
        label_encoding={"normal": 0, "anomaly": 1},
        files=(
            DatasetFile(
                logical_role="legacy_measurements",
                relative_path="legacy.csv",
                sha256=HASH_A,
                bytes=200,
                rows_excluding_header=20,
            ),
        ),
    )


def legacy_data_view_manifest() -> DataViewManifest:
    source = legacy_dataset_manifest()
    return DataViewManifest(
        name=DataViewName.CANONICAL_RULE,
        sampling_period_seconds=1.0,
        preprocessing_config={"legacy": True},
        upstream_dataset_manifest_id=source.manifest_id,
        fingerprint=HASH_C,
        source_view="legacy_canonical",
    )


def legacy_split_manifest(role: SplitRole) -> SplitManifest:
    source = legacy_dataset_manifest()
    view = legacy_data_view_manifest()
    return SplitManifest(
        dataset_manifest_id=source.manifest_id,
        data_view_id=view.view_id,
        role=role,
        raw_index_ranges=((0, 30),),
        purge_gap_samples=5,
        seed=11,
    )
