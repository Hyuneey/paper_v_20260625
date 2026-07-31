"""Explicit, loss-reporting adapters from legacy v1 data contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

from paperworks.data.contracts import (
    DataViewManifest,
    DataViewName,
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
    V2_SCHEMA_VERSION,
    stable_hash_v2,
)


class AdapterStatusV2(str, Enum):
    CREATED = "created"
    PENDING_CONTEXT = "pending_context"
    UNSUPPORTED_SOURCE = "unsupported_source"
    INVALID_SOURCE = "invalid_source"


T = TypeVar("T")


@dataclass(frozen=True)
class LegacySealedPolicyContextV2:
    policy_reference: str
    preregistered: bool
    explicit_approval_recorded: bool
    source_previously_exposed: bool

    def __post_init__(self) -> None:
        if not self.policy_reference:
            raise ValueError("policy_reference is required")


@dataclass(frozen=True)
class DataAdapterResultV2(Generic[T]):
    source_artifact_type: str
    source_artifact_hash: str
    requested_target_role: str | None
    status: AdapterStatusV2
    target_artifact_type: str | None
    target_artifact_hash: str | None
    information_loss: tuple[str, ...]
    sealed_access_granted: bool
    artifact: T | None = field(default=None, repr=False, compare=False)
    schema_version: str = V2_SCHEMA_VERSION
    artifact_type: str = "data_adapter_result_v2"

    def __post_init__(self) -> None:
        if self.sealed_access_granted:
            raise ValueError("legacy adapters cannot grant sealed access")
        if self.status is AdapterStatusV2.CREATED:
            if self.artifact is None or not self.target_artifact_hash:
                raise ValueError("created adapter results require a target artifact")
        elif self.artifact is not None or self.target_artifact_hash is not None:
            raise ValueError("non-created adapter results cannot contain a target artifact")

    def _content_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "source_artifact_type": self.source_artifact_type,
            "source_artifact_hash": self.source_artifact_hash,
            "requested_target_role": self.requested_target_role,
            "status": self.status.value,
            "target_artifact_type": self.target_artifact_type,
            "target_artifact_hash": self.target_artifact_hash,
            "information_loss": list(self.information_loss),
            "sealed_access_granted": self.sealed_access_granted,
        }

    @property
    def result_hash(self) -> str:
        return stable_hash_v2(self._content_dict())

    def to_dict(self) -> dict[str, object]:
        result = self._content_dict()
        result["artifact_hash"] = self.result_hash
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


def _failed_result(
    *,
    source_type: str,
    source_hash: str,
    requested_role: SplitRoleV2 | None,
    status: AdapterStatusV2,
    information_loss: tuple[str, ...],
) -> DataAdapterResultV2[object]:
    return DataAdapterResultV2(
        source_artifact_type=source_type,
        source_artifact_hash=source_hash,
        requested_target_role=requested_role.value if requested_role else None,
        status=status,
        target_artifact_type=None,
        target_artifact_hash=None,
        information_loss=information_loss,
        sealed_access_granted=False,
    )


def adapt_dataset_manifest_v1(
    source: DatasetManifest,
    *,
    creation_metadata: CreationMetadataV2,
    license_or_terms_reference: str = "unverified",
    citation_reference: str = "unverified",
) -> DataAdapterResultV2[DatasetManifestV2]:
    """Adapt dataset identity without inferring process or per-file labels."""

    try:
        files = tuple(
            DatasetFileV2(
                logical_file_role=item.logical_role,
                relative_local_path=item.relative_path.replace("\\", "/"),
                sha256=item.sha256,
                byte_size=item.bytes,
                row_count=item.rows_excluding_header,
                compression=CompressionTypeV2.UNKNOWN,
                time_range=None,
                process_ids=None,
                label_availability=LabelAvailabilityV2.UNKNOWN,
                provenance_status=ProvenanceStatusV2.UNVERIFIED,
            )
            for item in source.files
        )
        represented_paths = {item.relative_local_path for item in files}
        files += tuple(
                DatasetFileV2(
                    logical_file_role="legacy_file",
                    relative_local_path=path.replace("\\", "/"),
                    sha256=digest,
                    byte_size=None,
                    row_count=None,
                    compression=CompressionTypeV2.UNKNOWN,
                    time_range=None,
                    process_ids=None,
                    label_availability=LabelAvailabilityV2.UNKNOWN,
                    provenance_status=ProvenanceStatusV2.UNVERIFIED,
                )
                for path, digest in sorted(source.file_fingerprints.items())
                if path.replace("\\", "/") not in represented_paths
            )
        artifact = DatasetManifestV2(
            dataset_name=source.dataset_name,
            dataset_version_or_edition=source.dataset_edition,
            source_kind=source.source_kind or "unknown",
            source_reference=source.source_reference or "unknown",
            license_or_terms_reference=license_or_terms_reference,
            citation_reference=citation_reference,
            local_only_storage=True,
            files=files,
            feature_count=source.feature_count,
            feature_names_hash=source.feature_names_hash,
            timestamp_specification=TimestampSpecificationV2(
                field_name=source.timestamp_column,
                format=None,
                timezone=None,
                provenance_status=ProvenanceStatusV2.UNVERIFIED,
            ),
            nominal_sampling_interval_seconds=source.sampling_period_seconds,
            label_specification=LabelSpecificationV2(
                field_name=source.label_column,
                encoding=source.label_encoding,
                provenance_status=ProvenanceStatusV2.UNVERIFIED,
            ),
            available_process_ids=None,
            metadata_artifact_references=(source.manifest_id,),
            provenance_status=ProvenanceStatusV2.UNVERIFIED,
            creation_metadata=creation_metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _failed_result(
            source_type="DatasetManifest",
            source_hash=source.manifest_id,
            requested_role=None,
            status=AdapterStatusV2.INVALID_SOURCE,
            information_loss=(f"invalid_source:{type(exc).__name__}",),
        )
    return DataAdapterResultV2(
        source_artifact_type="DatasetManifest",
        source_artifact_hash=source.manifest_id,
        requested_target_role=None,
        status=AdapterStatusV2.CREATED,
        target_artifact_type=artifact.artifact_type,
        target_artifact_hash=artifact.manifest_id,
        information_loss=(
            "compression_not_recorded_in_v1",
            "file_time_ranges_not_recorded_in_v1",
            "file_label_availability_not_recorded_in_v1",
            "process_scope_not_recorded_in_v1",
            "timestamp_format_and_timezone_not_recorded_in_v1",
        ),
        sealed_access_granted=False,
        artifact=artifact,
    )


def adapt_data_view_manifest_v1(
    source: DataViewManifest,
    *,
    creation_metadata: CreationMetadataV2,
    process_scope: tuple[str, ...] | None = None,
) -> DataAdapterResultV2[DataViewManifestV2]:
    """Adapt a v1 view while leaving unknown aggregation provenance explicit."""

    kind = (
        DataViewKindV2.CANONICAL_RULE
        if source.name is DataViewName.CANONICAL_RULE
        else DataViewKindV2.GDN
    )
    try:
        artifact = DataViewManifestV2(
            view_kind=kind,
            source_dataset_manifest_id=source.upstream_dataset_manifest_id,
            process_scope=process_scope,
            sampling_interval_seconds=source.sampling_period_seconds,
            preprocessing_config=source.preprocessing_config,
            aggregation=AggregationDescriptionV2(
                method="legacy_unspecified",
                source_sampling_interval_seconds=None,
                output_sampling_interval_seconds=source.sampling_period_seconds,
                explicit=False,
                description="Legacy v1 does not record source sampling or aggregation.",
            ),
            feature_order_hash=source.fingerprint,
            second_level_rule_calibration_allowed=False,
            provenance_status=ProvenanceStatusV2.UNVERIFIED,
            creation_metadata=creation_metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _failed_result(
            source_type="DataViewManifest",
            source_hash=source.view_id,
            requested_role=None,
            status=AdapterStatusV2.INVALID_SOURCE,
            information_loss=(f"invalid_source:{type(exc).__name__}",),
        )
    return DataAdapterResultV2(
        source_artifact_type="DataViewManifest",
        source_artifact_hash=source.view_id,
        requested_target_role=None,
        status=AdapterStatusV2.CREATED,
        target_artifact_type=artifact.artifact_type,
        target_artifact_hash=artifact.view_id,
        information_loss=(
            "source_sampling_interval_not_recorded_in_v1",
            "aggregation_method_not_recorded_in_v1",
        )
        + (
            ("process_scope_explicitly_unset",)
            if process_scope is None
            else ()
        )
        + ("legacy_fingerprint_used_as_feature_order_hash",),
        sealed_access_granted=False,
        artifact=artifact,
    )


def _resolve_split_target(
    source_role: SplitRole,
    requested_role: SplitRoleV2 | None,
    sealed_policy_context: LegacySealedPolicyContextV2 | None,
) -> tuple[AdapterStatusV2, tuple[str, ...]]:
    if requested_role is None:
        return AdapterStatusV2.PENDING_CONTEXT, ("explicit_target_role_required",)
    if source_role is SplitRole.TRAIN_NORMAL:
        if requested_role is SplitRoleV2.NORMAL_CANDIDATE_FIT:
            return AdapterStatusV2.CREATED, ()
        return AdapterStatusV2.UNSUPPORTED_SOURCE, ("legacy_train_normal_role_mismatch",)
    if source_role is SplitRole.CALIBRATION_NORMAL:
        if requested_role is SplitRoleV2.NORMAL_RELATION_CALIBRATION:
            return AdapterStatusV2.CREATED, ()
        return AdapterStatusV2.UNSUPPORTED_SOURCE, (
            "legacy_calibration_normal_role_mismatch",
        )
    if source_role is SplitRole.VALIDATION:
        if requested_role in {
            SplitRoleV2.DEVELOPMENT,
            SplitRoleV2.INNER_UTILITY,
            SplitRoleV2.OUTER_VALIDATION,
        }:
            return AdapterStatusV2.CREATED, (
                "legacy_validation_semantics_supplied_by_external_context",
            )
        return AdapterStatusV2.UNSUPPORTED_SOURCE, (
            "legacy_validation_cannot_map_to_requested_role",
        )
    if requested_role is not SplitRoleV2.SEALED_EVALUATION:
        return AdapterStatusV2.UNSUPPORTED_SOURCE, (
            "legacy_test_cannot_map_to_nonsealed_role",
        )
    if sealed_policy_context is None:
        return AdapterStatusV2.PENDING_CONTEXT, (
            "explicit_sealed_policy_context_required",
        )
    if sealed_policy_context.source_previously_exposed:
        return AdapterStatusV2.UNSUPPORTED_SOURCE, (
            "previously_exposed_legacy_test_is_not_fresh_sealed_data",
        )
    if not (
        sealed_policy_context.preregistered
        and sealed_policy_context.explicit_approval_recorded
    ):
        return AdapterStatusV2.PENDING_CONTEXT, (
            "sealed_preregistration_and_approval_required",
        )
    return AdapterStatusV2.CREATED, (
        "sealed_access_not_granted_by_adapter",
        "legacy_test_semantics_supplied_by_external_policy",
    )


def adapt_split_manifest_v1(
    source: SplitManifest,
    *,
    requested_target_role: SplitRoleV2 | None,
    creation_metadata: CreationMetadataV2,
    process_scope: tuple[str, ...] | None,
    sealed_policy_context: LegacySealedPolicyContextV2 | None = None,
) -> DataAdapterResultV2[SplitManifestV2]:
    """Adapt a split only after its ambiguous role context is explicit."""

    status, loss = _resolve_split_target(
        source.role, requested_target_role, sealed_policy_context
    )
    if status is not AdapterStatusV2.CREATED:
        return _failed_result(
            source_type="SplitManifest",
            source_hash=source.split_id,
            requested_role=requested_target_role,
            status=status,
            information_loss=loss,
        )
    if process_scope is None:
        return _failed_result(
            source_type="SplitManifest",
            source_hash=source.split_id,
            requested_role=requested_target_role,
            status=AdapterStatusV2.PENDING_CONTEXT,
            information_loss=loss + ("explicit_process_scope_required",),
        )
    assert requested_target_role is not None
    try:
        artifact = SplitManifestV2(
            dataset_manifest_id=source.dataset_manifest_id,
            data_view_id=source.data_view_id,
            role=requested_target_role,
            raw_ranges=tuple(
                RawRangeV2(start=start, end=end)
                for start, end in source.raw_index_ranges
            ),
            event_ids=None,
            purge_gap_samples=source.purge_gap_samples,
            process_scope=process_scope,
            seed=source.seed,
            creation_policy="legacy_v1_explicit_context_adapter",
            provenance_status=ProvenanceStatusV2.UNVERIFIED,
            sealed_access_status=(
                SealedAccessStatusV2.APPROVAL_REQUIRED
                if requested_target_role is SplitRoleV2.SEALED_EVALUATION
                else SealedAccessStatusV2.NOT_APPLICABLE
            ),
            split_before_windowing=True,
            creation_metadata=creation_metadata,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return _failed_result(
            source_type="SplitManifest",
            source_hash=source.split_id,
            requested_role=requested_target_role,
            status=AdapterStatusV2.INVALID_SOURCE,
            information_loss=loss + (f"invalid_source:{type(exc).__name__}",),
        )
    return DataAdapterResultV2(
        source_artifact_type="SplitManifest",
        source_artifact_hash=source.split_id,
        requested_target_role=requested_target_role.value,
        status=AdapterStatusV2.CREATED,
        target_artifact_type=artifact.artifact_type,
        target_artifact_hash=artifact.split_id,
        information_loss=loss
        + (
            "event_ids_not_recorded_in_v1",
            "creation_policy_not_recorded_in_v1",
            "sealed_access_never_granted_by_adapter",
        ),
        sealed_access_granted=False,
        artifact=artifact,
    )
