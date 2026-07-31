"""Serialized legacy relation adapter for normal-only v6 evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from paperworks.data.contracts_v2 import SplitRoleV2
from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    canonical_json_v1,
    deterministic_id,
    freeze_json,
    reject_unknown_fields,
    require_sha256,
    require_unique_strings,
    stable_hash_v1,
    thaw_json,
    verify_identity_fields,
)
from paperworks.v6.normal_evidence_v1 import (
    CalibrationParameterReferenceV1,
    CalibrationParameterRoleV1,
    DistributionSummaryV1,
    EvidenceStatusV1,
    NormalRelationEvidenceV1,
    OperatingRegimeStatusV1,
    RelationStabilitySummaryV1,
    RelationSupportSummaryV1,
    ResponseDirectionV1,
)


ADAPTER_RESULT_ARTIFACT_TYPE = "v6_evidence_adapter_result"
_REQUIRED_CONTEXT_FIELDS = frozenset(
    {
        "dataset_manifest_id",
        "data_view_id",
        "split_manifest_id",
        "target_split_role",
        "process_scope",
        "operating_regime_id",
        "operating_regime_condition_refs",
        "source_metadata_ref",
        "target_metadata_ref",
        "candidate_universe_ref",
        "candidate_edge_refs",
        "matched_normal_reference_refs",
        "stability_summary",
        "calibration_parameter_refs",
        "response_direction",
        "creation_metadata",
    }
)


class V6EvidenceAdapterStatusV1(str, Enum):
    CREATED = "created"
    PENDING_CONTEXT = "pending_context"
    UNSUPPORTED_SOURCE = "unsupported_source"
    INVALID_SOURCE = "invalid_source"


@dataclass(frozen=True)
class V6EvidenceAdapterResultV1:
    source_artifact_types: tuple[str, ...]
    source_artifact_hashes: tuple[str, ...]
    requested_target_split_role: str | None
    status: V6EvidenceAdapterStatusV1
    target_artifact_type: str | None
    target_evidence_id: str | None
    target_artifact_hash: str | None
    information_loss: tuple[str, ...]
    rule_validity_granted: bool
    runtime_authority_granted: bool
    provenance_references: tuple[str, ...]
    creation_metadata: CreationMetadataV1
    artifact: NormalRelationEvidenceV1 | None = field(
        default=None, repr=False, compare=False
    )
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = ADAPTER_RESULT_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError("unsupported evidence adapter schema_version")
        if self.artifact_type != ADAPTER_RESULT_ARTIFACT_TYPE:
            raise V6FoundationError("invalid evidence adapter artifact_type")
        source_types = tuple(str(item) for item in self.source_artifact_types)
        if not source_types or any(not item for item in source_types):
            raise V6FoundationError(
                "source_artifact_types must contain non-empty values"
            )
        object.__setattr__(self, "source_artifact_types", source_types)
        if len(self.source_artifact_hashes) != len(self.source_artifact_types):
            raise V6FoundationError(
                "source artifact types and hashes must have equal length"
            )
        for index, digest in enumerate(self.source_artifact_hashes):
            require_sha256(digest, f"source_artifact_hashes[{index}]")
        object.__setattr__(
            self,
            "information_loss",
            require_unique_strings(
                self.information_loss, "information_loss", allow_empty=False
            ),
        )
        for index, digest in enumerate(self.provenance_references):
            require_sha256(digest, f"provenance_references[{index}]")
        if self.rule_validity_granted or self.runtime_authority_granted:
            raise V6FoundationError(
                "legacy evidence adapter cannot grant validity or runtime authority"
            )
        if self.status is V6EvidenceAdapterStatusV1.CREATED:
            if (
                self.target_artifact_type != "normal_relation_evidence"
                or self.target_evidence_id is None
                or self.target_artifact_hash is None
            ):
                raise V6FoundationError(
                    "created adapter result requires complete target identity"
                )
            require_sha256(self.target_artifact_hash, "target_artifact_hash")
            if self.artifact is not None and (
                self.artifact.evidence_id != self.target_evidence_id
                or self.artifact.artifact_hash != self.target_artifact_hash
            ):
                raise V6FoundationError(
                    "adapter target identity does not match the evidence artifact"
                )
        elif any(
            item is not None
            for item in (
                self.target_artifact_type,
                self.target_evidence_id,
                self.target_artifact_hash,
                self.artifact,
            )
        ):
            raise V6FoundationError(
                "non-created adapter result cannot emit a partial target"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "source_artifact_types": list(self.source_artifact_types),
            "source_artifact_hashes": list(self.source_artifact_hashes),
            "requested_target_split_role": self.requested_target_split_role,
            "status": self.status.value,
            "target_artifact_type": self.target_artifact_type,
            "target_evidence_id": self.target_evidence_id,
            "target_artifact_hash": self.target_artifact_hash,
            "information_loss": list(self.information_loss),
            "rule_validity_granted": self.rule_validity_granted,
            "runtime_authority_granted": self.runtime_authority_granted,
            "provenance_references": list(self.provenance_references),
            "creation_metadata": self.creation_metadata.to_dict(),
        }

    @property
    def adapter_result_id(self) -> str:
        return deterministic_id("VEAR-V1", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["adapter_result_id"] = self.adapter_result_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["adapter_result_id"] = self.adapter_result_id
        payload["artifact_hash"] = self.artifact_hash
        return payload

    def to_json(self) -> str:
        return canonical_json_v1(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "V6EvidenceAdapterResultV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "schema_version",
                    "artifact_type",
                    "adapter_result_id",
                    "artifact_hash",
                    "source_artifact_types",
                    "source_artifact_hashes",
                    "requested_target_split_role",
                    "status",
                    "target_artifact_type",
                    "target_evidence_id",
                    "target_artifact_hash",
                    "information_loss",
                    "rule_validity_granted",
                    "runtime_authority_granted",
                    "provenance_references",
                    "creation_metadata",
                }
            ),
            ADAPTER_RESULT_ARTIFACT_TYPE,
        )
        result = cls(
            source_artifact_types=tuple(
                str(item) for item in data["source_artifact_types"]
            ),
            source_artifact_hashes=tuple(
                str(item) for item in data["source_artifact_hashes"]
            ),
            requested_target_split_role=data.get("requested_target_split_role"),
            status=V6EvidenceAdapterStatusV1(str(data["status"])),
            target_artifact_type=data.get("target_artifact_type"),
            target_evidence_id=data.get("target_evidence_id"),
            target_artifact_hash=data.get("target_artifact_hash"),
            information_loss=tuple(
                str(item) for item in data["information_loss"]
            ),
            rule_validity_granted=data["rule_validity_granted"] is True,
            runtime_authority_granted=data["runtime_authority_granted"] is True,
            provenance_references=tuple(
                str(item) for item in data["provenance_references"]
            ),
            creation_metadata=CreationMetadataV1.from_dict(
                data["creation_metadata"]
            ),
            schema_version=str(
                data.get("schema_version", V6_FOUNDATION_SCHEMA_VERSION)
            ),
            artifact_type=str(
                data.get("artifact_type", ADAPTER_RESULT_ARTIFACT_TYPE)
            ),
        )
        verify_identity_fields(
            data,
            id_field="adapter_result_id",
            observed_id=result.adapter_result_id,
            observed_hash=result.artifact_hash,
        )
        return result

    @classmethod
    def from_json(cls, text: str) -> "V6EvidenceAdapterResultV1":
        document = json.loads(text)
        if not isinstance(document, dict):
            raise V6FoundationError("adapter result must be a JSON object")
        return cls.from_dict(document)


def _source_snapshot(
    value: Mapping[str, Any], *, omitted_fields: frozenset[str] = frozenset()
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in value:
        if not isinstance(key, str):
            raise V6FoundationError("serialized source keys must be strings")
        if key in omitted_fields:
            continue
        result[key] = thaw_json(freeze_json(value[key]))
    return result


def _source_identity(
    profile: Mapping[str, Any], evidence_pack: Mapping[str, Any]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    profile_type = str(profile.get("artifact_type", "unknown"))
    pack_type = str(evidence_pack.get("artifact_type", "unknown"))
    legacy_profile_id = evidence_pack.get("relation_profile_id")
    profile_hash = (
        str(legacy_profile_id)
        if isinstance(legacy_profile_id, str)
        and len(legacy_profile_id) == 64
        else stable_hash_v1(profile)
    )
    return (
        (profile_type, pack_type),
        (profile_hash, stable_hash_v1(evidence_pack)),
    )


def _failed_result(
    *,
    source_types: tuple[str, ...],
    source_hashes: tuple[str, ...],
    requested_role: str | None,
    status: V6EvidenceAdapterStatusV1,
    information_loss: tuple[str, ...],
    creation_metadata: CreationMetadataV1,
) -> V6EvidenceAdapterResultV1:
    return V6EvidenceAdapterResultV1(
        source_artifact_types=source_types,
        source_artifact_hashes=source_hashes,
        requested_target_split_role=requested_role,
        status=status,
        target_artifact_type=None,
        target_evidence_id=None,
        target_artifact_hash=None,
        information_loss=information_loss,
        rule_validity_granted=False,
        runtime_authority_granted=False,
        provenance_references=source_hashes,
        creation_metadata=creation_metadata,
    )


def _legacy_summary(
    data: Mapping[str, Any],
    *,
    unit: str,
    method: str,
    value_semantics: str,
) -> DistributionSummaryV1:
    required = {"count", "min", "p50", "max"}
    if not required.issubset(data):
        raise V6FoundationError("legacy summary fields are incomplete")
    count_number = float(data["count"])
    if not count_number.is_integer():
        raise V6FoundationError("legacy summary count is not integral")
    return DistributionSummaryV1(
        count=int(count_number),
        minimum=float(data["min"]),
        p50=float(data["p50"]),
        p95=float(data["p95"]) if data.get("p95") is not None else None,
        maximum=float(data["max"]),
        unit=unit,
        method=method,
        value_semantics=value_semantics,
    )


def adapt_serialized_legacy_relation_evidence_v1(
    relation_profile: Mapping[str, Any],
    relation_evidence_pack: Mapping[str, Any],
    *,
    external_context: Mapping[str, Any],
) -> V6EvidenceAdapterResultV1:
    """Adapt aggregate legacy relation mappings without importing legacy classes."""

    default_metadata = CreationMetadataV1(
        created_at="1970-01-01T00:00:00Z",
        created_by="pending_context",
        code_commit="unverified",
    )
    try:
        profile = _source_snapshot(
            relation_profile,
            omitted_fields=frozenset({"trigger_events", "response_events"}),
        )
        pack = _source_snapshot(relation_evidence_pack)
        context = _source_snapshot(external_context)
        source_types, source_hashes = _source_identity(profile, pack)
        creation_raw = context.get("creation_metadata")
        creation_metadata = (
            CreationMetadataV1.from_dict(creation_raw)
            if isinstance(creation_raw, Mapping)
            else default_metadata
        )
    except (TypeError, ValueError, V6FoundationError):
        return _failed_result(
            source_types=("unknown", "unknown"),
            source_hashes=("0" * 64, "1" * 64),
            requested_role=None,
            status=V6EvidenceAdapterStatusV1.INVALID_SOURCE,
            information_loss=("invalid_serialized_source",),
            creation_metadata=default_metadata,
        )
    requested_role = (
        str(context["target_split_role"])
        if "target_split_role" in context
        else None
    )
    if source_types != ("relation_profile", "relation_evidence_pack"):
        return _failed_result(
            source_types=source_types,
            source_hashes=source_hashes,
            requested_role=requested_role,
            status=V6EvidenceAdapterStatusV1.INVALID_SOURCE,
            information_loss=("unexpected_legacy_artifact_type",),
            creation_metadata=creation_metadata,
        )
    missing_context = tuple(sorted(_REQUIRED_CONTEXT_FIELDS - set(context)))
    if missing_context:
        return _failed_result(
            source_types=source_types,
            source_hashes=source_hashes,
            requested_role=requested_role,
            status=V6EvidenceAdapterStatusV1.PENDING_CONTEXT,
            information_loss=tuple(
                f"missing_external_context:{item}" for item in missing_context
            ),
            creation_metadata=creation_metadata,
        )
    if profile.get("split_name") != "calibration_normal":
        return _failed_result(
            source_types=source_types,
            source_hashes=source_hashes,
            requested_role=requested_role,
            status=V6EvidenceAdapterStatusV1.UNSUPPORTED_SOURCE,
            information_loss=("legacy_source_split_is_not_calibration_normal",),
            creation_metadata=creation_metadata,
        )
    if requested_role != SplitRoleV2.NORMAL_RELATION_CALIBRATION.value:
        return _failed_result(
            source_types=source_types,
            source_hashes=source_hashes,
            requested_role=requested_role,
            status=V6EvidenceAdapterStatusV1.UNSUPPORTED_SOURCE,
            information_loss=(
                "explicit_normal_relation_calibration_target_required",
            ),
            creation_metadata=creation_metadata,
        )
    if (
        profile.get("relation_type")
        != "binary_actuator_to_continuous_sensor"
        or pack.get("relation_type")
        != "binary_actuator_to_continuous_sensor"
    ):
        return _failed_result(
            source_types=source_types,
            source_hashes=source_hashes,
            requested_role=requested_role,
            status=V6EvidenceAdapterStatusV1.UNSUPPORTED_SOURCE,
            information_loss=("legacy_relation_family_is_not_supported",),
            creation_metadata=creation_metadata,
        )
    try:
        if (
            profile["source"] != pack["source"]
            or profile["target"] != pack["target"]
        ):
            raise V6FoundationError("legacy source/target mismatch")
        if (
            profile.get("source_view") != "canonical_rule_view"
            or pack.get("source_view") != "canonical_rule_view"
        ):
            raise V6FoundationError("legacy source view is incompatible")
        require_sha256(str(pack["relation_profile_id"]), "relation_profile_id")
        support_counts = pack["support_counts"]
        trigger_count = int(profile["trigger_count"])
        matched_count = int(profile["matched_response_count"])
        missing_count = int(profile["missing_response_count"])
        right_censored_count = int(profile["right_censored_count"])
        if any(
            int(support_counts[name]) != expected
            for name, expected in (
                ("trigger_count", trigger_count),
                ("matched_response_count", matched_count),
                ("missing_response_count", missing_count),
                ("right_censored_count", right_censored_count),
            )
        ):
            raise V6FoundationError("legacy support summaries disagree")
        support = RelationSupportSummaryV1(
            trigger_count=trigger_count,
            evaluable_trigger_count=matched_count + missing_count,
            matched_response_count=matched_count,
            missing_response_count=missing_count,
            right_censored_count=right_censored_count,
        )
        lag_summary = _legacy_summary(
            profile["delay_summary_seconds"],
            unit="seconds",
            method="legacy_relation_profile_summary",
            value_semantics="lag",
        )
        magnitude_summary = _legacy_summary(
            profile["magnitude_summary"],
            unit=str(context.get("response_magnitude_unit", "unverified")),
            method="legacy_relation_profile_summary",
            value_semantics="absolute_response_magnitude",
        )
        stability = RelationStabilitySummaryV1.from_dict(
            context["stability_summary"]
        )
        parameter_mapping = context["calibration_parameter_refs"]
        if not isinstance(parameter_mapping, Mapping):
            raise V6FoundationError(
                "calibration_parameter_refs must be a role mapping"
            )
        parameter_refs = tuple(
            CalibrationParameterReferenceV1(
                role=CalibrationParameterRoleV1(str(role)),
                artifact_ref=str(reference),
            )
            for role, reference in sorted(parameter_mapping.items())
        )
        legacy_status = str(profile["normal_support_status"])
        if legacy_status == "supported":
            evidence_status = EvidenceStatusV1.SUPPORTED
            insufficiency_reasons: tuple[str, ...] = ()
        elif legacy_status == "INSUFFICIENT_NORMAL_SUPPORT":
            evidence_status = EvidenceStatusV1.INSUFFICIENT_SUPPORT
            insufficiency_reasons = tuple(
                str(item)
                for item in context.get(
                    "evidence_insufficiency_reasons",
                    ("insufficient_matched_response_support",),
                )
            )
        else:
            raise V6FoundationError("legacy normal support status is invalid")
        artifact = NormalRelationEvidenceV1(
            dataset_manifest_id=str(context["dataset_manifest_id"]),
            data_view_id=str(context["data_view_id"]),
            split_manifest_id=str(context["split_manifest_id"]),
            split_role=SplitRoleV2(str(context["target_split_role"])),
            process_scope=tuple(str(item) for item in context["process_scope"]),
            source_variable=str(profile["source"]),
            target_variable=str(profile["target"]),
            source_metadata_ref=str(context["source_metadata_ref"]),
            target_metadata_ref=str(context["target_metadata_ref"]),
            candidate_universe_ref=str(context["candidate_universe_ref"]),
            candidate_edge_refs=tuple(
                str(item) for item in context["candidate_edge_refs"]
            ),
            relation_family="delayed_response",
            response_direction=ResponseDirectionV1(
                str(context["response_direction"])
            ),
            operating_regime_id=str(context["operating_regime_id"]),
            operating_regime_status=OperatingRegimeStatusV1(
                str(context.get("operating_regime_status", "unverified"))
            ),
            operating_regime_condition_refs=tuple(
                str(item)
                for item in context["operating_regime_condition_refs"]
            ),
            support_summary=support,
            lag_summary=lag_summary,
            response_magnitude_summary=magnitude_summary,
            persistence_summary=None,
            stability_summary=stability,
            evidence_status=evidence_status,
            evidence_insufficiency_reasons=insufficiency_reasons,
            matched_normal_reference_refs=tuple(
                str(item)
                for item in context["matched_normal_reference_refs"]
            ),
            calibration_parameter_refs=parameter_refs,
            provenance_references=source_hashes
            + tuple(
                str(item)
                for item in context.get("provenance_references", ())
            ),
            creation_metadata=creation_metadata,
            raw_values_included=False,
            label_performance_used=False,
            detector_context_used=False,
            prohibited_claims=(
                "physical_causality",
                "root_cause",
                "universal_invariant",
            ),
            validity_authority_granted=False,
            runtime_authority_granted=False,
            claim_boundary=(
                "Aggregate normal delayed-response evidence only; no causal, "
                "validity, governance, or runtime-authority claim."
            ),
        )
    except (KeyError, TypeError, ValueError, V6FoundationError):
        return _failed_result(
            source_types=source_types,
            source_hashes=source_hashes,
            requested_role=requested_role,
            status=V6EvidenceAdapterStatusV1.INVALID_SOURCE,
            information_loss=("invalid_or_incomplete_legacy_aggregate_semantics",),
            creation_metadata=creation_metadata,
        )
    loss = [
        "legacy_schema_identity_not_reused",
        "legacy_dataset_field_retained_by_source_hash_only",
        "legacy_data_fingerprint_retained_by_source_hash_only",
        "legacy_config_hash_retained_by_source_hash_only",
        "legacy_code_commit_retained_by_source_hash_only",
        "legacy_random_seed_retained_by_source_hash_only",
        "legacy_created_at_retained_by_source_hash_only",
        "legacy_source_view_replaced_by_data_view_reference",
        "legacy_sampling_period_replaced_by_data_view_reference",
        "legacy_overlapping_window_count_not_mapped",
        "legacy_upstream_artifact_ids_retained_by_source_hash_only",
        "legacy_trigger_events_not_copied",
        "legacy_response_events_not_copied",
        "legacy_profile_hash_preserved_without_raw_event_rehash",
        "legacy_summary_mean_not_mapped",
        "legacy_recommended_rule_family_not_mapped",
        "legacy_relation_profile_id_represented_as_provenance",
        "legacy_calibration_record_ids_replaced_by_external_parameter_refs",
        "legacy_calibrated_values_not_copied",
        "legacy_persistence_summary_unavailable",
        "legacy_relation_does_not_establish_causality",
        "adapter_grants_no_validity_or_runtime_authority",
    ]
    if profile["delay_summary_seconds"].get("p95") is None:
        loss.append("legacy_lag_p95_unavailable")
    if profile["magnitude_summary"].get("p95") is None:
        loss.append("legacy_magnitude_p95_unavailable")
    if "response_magnitude_unit" not in context:
        loss.append("legacy_magnitude_unit_unverified")
    return V6EvidenceAdapterResultV1(
        source_artifact_types=source_types,
        source_artifact_hashes=source_hashes,
        requested_target_split_role=requested_role,
        status=V6EvidenceAdapterStatusV1.CREATED,
        target_artifact_type=artifact.artifact_type,
        target_evidence_id=artifact.evidence_id,
        target_artifact_hash=artifact.artifact_hash,
        information_loss=tuple(loss),
        rule_validity_granted=False,
        runtime_authority_granted=False,
        provenance_references=source_hashes,
        creation_metadata=creation_metadata,
        artifact=artifact,
    )
