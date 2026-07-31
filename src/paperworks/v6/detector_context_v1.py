"""Optional reference-only detector error context for v6 development and utility."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from paperworks.data.contracts_v2 import SplitRoleV2
from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    canonical_json_v1,
    deterministic_id,
    reject_unknown_fields,
    require_sha256,
    require_sha256_refs,
    require_unique_strings,
    stable_hash_v1,
    verify_identity_fields,
)


DETECTOR_CONTEXT_ARTIFACT_TYPE = "detector_error_context"


class DetectorErrorDirectionV1(str, Enum):
    FALSE_NEGATIVE = "false_negative"
    FALSE_POSITIVE = "false_positive"


class DetectorContextPurposeV1(str, Enum):
    DEVELOPMENT_DIAGNOSTIC = "development_diagnostic"
    INNER_UTILITY_ASSESSMENT = "inner_utility_assessment"


@dataclass(frozen=True)
class DetectorErrorContextV1:
    dataset_manifest_id: str
    data_view_id: str
    split_manifest_id: str
    split_role: SplitRoleV2
    process_scope: tuple[str, ...]
    normal_relation_evidence_ref: str
    error_direction: DetectorErrorDirectionV1
    detector_artifact_ref: str
    detector_config_ref: str
    detector_prediction_ref: str
    event_refs: tuple[str, ...]
    context_window_refs: tuple[str, ...]
    purpose: DetectorContextPurposeV1
    supplementary_only: bool
    primary_correction_direction: bool
    provenance_references: tuple[str, ...]
    creation_metadata: CreationMetadataV1
    raw_values_included: bool
    outer_data_used: bool
    sealed_data_used: bool
    replaces_normal_evidence: bool
    validity_authority_granted: bool
    runtime_authority_granted: bool
    claim_boundary: str
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = DETECTOR_CONTEXT_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError("unsupported detector context schema_version")
        if self.artifact_type != DETECTOR_CONTEXT_ARTIFACT_TYPE:
            raise V6FoundationError("invalid detector context artifact_type")
        for field_name, value in (
            ("dataset_manifest_id", self.dataset_manifest_id),
            ("data_view_id", self.data_view_id),
            ("split_manifest_id", self.split_manifest_id),
            ("normal_relation_evidence_ref", self.normal_relation_evidence_ref),
            ("detector_artifact_ref", self.detector_artifact_ref),
            ("detector_config_ref", self.detector_config_ref),
            ("detector_prediction_ref", self.detector_prediction_ref),
        ):
            require_sha256(value, field_name)
        if self.split_role not in {
            SplitRoleV2.DEVELOPMENT,
            SplitRoleV2.INNER_UTILITY,
        }:
            raise V6FoundationError(
                "detector context is allowed only on development or inner_utility"
            )
        if (
            self.split_role is SplitRoleV2.DEVELOPMENT
            and self.purpose is not DetectorContextPurposeV1.DEVELOPMENT_DIAGNOSTIC
        ):
            raise V6FoundationError(
                "development context requires development_diagnostic purpose"
            )
        if (
            self.split_role is SplitRoleV2.INNER_UTILITY
            and self.purpose
            is not DetectorContextPurposeV1.INNER_UTILITY_ASSESSMENT
        ):
            raise V6FoundationError(
                "inner_utility context requires inner_utility_assessment purpose"
            )
        object.__setattr__(
            self,
            "process_scope",
            require_unique_strings(
                self.process_scope, "process_scope", allow_empty=False
            ),
        )
        object.__setattr__(
            self, "event_refs", require_sha256_refs(self.event_refs, "event_refs")
        )
        object.__setattr__(
            self,
            "context_window_refs",
            require_sha256_refs(self.context_window_refs, "context_window_refs"),
        )
        object.__setattr__(
            self,
            "provenance_references",
            require_sha256_refs(
                self.provenance_references,
                "provenance_references",
                allow_empty=False,
            ),
        )
        if (
            self.error_direction is DetectorErrorDirectionV1.FALSE_POSITIVE
            and not self.supplementary_only
        ):
            raise V6FoundationError(
                "false-positive detector context must be supplementary_only"
            )
        if (
            self.error_direction is DetectorErrorDirectionV1.FALSE_POSITIVE
            and self.primary_correction_direction
        ):
            raise V6FoundationError(
                "false-positive context cannot be the primary correction direction"
            )
        if self.raw_values_included:
            raise V6FoundationError("detector context cannot contain raw values")
        if self.outer_data_used or self.sealed_data_used:
            raise V6FoundationError(
                "detector context cannot use outer or sealed data"
            )
        if self.replaces_normal_evidence:
            raise V6FoundationError(
                "detector context cannot replace normal relation evidence"
            )
        if self.validity_authority_granted or self.runtime_authority_granted:
            raise V6FoundationError(
                "detector context cannot grant validity or runtime authority"
            )
        if not self.claim_boundary:
            raise V6FoundationError("claim_boundary is required")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
            "split_manifest_id": self.split_manifest_id,
            "split_role": self.split_role.value,
            "process_scope": list(self.process_scope),
            "normal_relation_evidence_ref": self.normal_relation_evidence_ref,
            "error_direction": self.error_direction.value,
            "detector_artifact_ref": self.detector_artifact_ref,
            "detector_config_ref": self.detector_config_ref,
            "detector_prediction_ref": self.detector_prediction_ref,
            "event_refs": list(self.event_refs),
            "context_window_refs": list(self.context_window_refs),
            "purpose": self.purpose.value,
            "supplementary_only": self.supplementary_only,
            "primary_correction_direction": self.primary_correction_direction,
            "provenance_references": list(self.provenance_references),
            "creation_metadata": self.creation_metadata.to_dict(),
            "raw_values_included": self.raw_values_included,
            "outer_data_used": self.outer_data_used,
            "sealed_data_used": self.sealed_data_used,
            "replaces_normal_evidence": self.replaces_normal_evidence,
            "validity_authority_granted": self.validity_authority_granted,
            "runtime_authority_granted": self.runtime_authority_granted,
            "claim_boundary": self.claim_boundary,
        }

    @property
    def context_id(self) -> str:
        return deterministic_id("DEC-V1", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["context_id"] = self.context_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["context_id"] = self.context_id
        payload["artifact_hash"] = self.artifact_hash
        return payload

    def to_json(self) -> str:
        return canonical_json_v1(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DetectorErrorContextV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "schema_version",
                    "artifact_type",
                    "context_id",
                    "artifact_hash",
                    "dataset_manifest_id",
                    "data_view_id",
                    "split_manifest_id",
                    "split_role",
                    "process_scope",
                    "normal_relation_evidence_ref",
                    "error_direction",
                    "detector_artifact_ref",
                    "detector_config_ref",
                    "detector_prediction_ref",
                    "event_refs",
                    "context_window_refs",
                    "purpose",
                    "supplementary_only",
                    "primary_correction_direction",
                    "provenance_references",
                    "creation_metadata",
                    "raw_values_included",
                    "outer_data_used",
                    "sealed_data_used",
                    "replaces_normal_evidence",
                    "validity_authority_granted",
                    "runtime_authority_granted",
                    "claim_boundary",
                }
            ),
            DETECTOR_CONTEXT_ARTIFACT_TYPE,
        )
        result = cls(
            dataset_manifest_id=str(data["dataset_manifest_id"]),
            data_view_id=str(data["data_view_id"]),
            split_manifest_id=str(data["split_manifest_id"]),
            split_role=SplitRoleV2(str(data["split_role"])),
            process_scope=tuple(str(item) for item in data["process_scope"]),
            normal_relation_evidence_ref=str(
                data["normal_relation_evidence_ref"]
            ),
            error_direction=DetectorErrorDirectionV1(str(data["error_direction"])),
            detector_artifact_ref=str(data["detector_artifact_ref"]),
            detector_config_ref=str(data["detector_config_ref"]),
            detector_prediction_ref=str(data["detector_prediction_ref"]),
            event_refs=tuple(str(item) for item in data["event_refs"]),
            context_window_refs=tuple(
                str(item) for item in data["context_window_refs"]
            ),
            purpose=DetectorContextPurposeV1(str(data["purpose"])),
            supplementary_only=data["supplementary_only"] is True,
            primary_correction_direction=data["primary_correction_direction"] is True,
            provenance_references=tuple(
                str(item) for item in data["provenance_references"]
            ),
            creation_metadata=CreationMetadataV1.from_dict(
                data["creation_metadata"]
            ),
            raw_values_included=data["raw_values_included"] is True,
            outer_data_used=data["outer_data_used"] is True,
            sealed_data_used=data["sealed_data_used"] is True,
            replaces_normal_evidence=data["replaces_normal_evidence"] is True,
            validity_authority_granted=data["validity_authority_granted"] is True,
            runtime_authority_granted=data["runtime_authority_granted"] is True,
            claim_boundary=str(data["claim_boundary"]),
            schema_version=str(
                data.get("schema_version", V6_FOUNDATION_SCHEMA_VERSION)
            ),
            artifact_type=str(
                data.get("artifact_type", DETECTOR_CONTEXT_ARTIFACT_TYPE)
            ),
        )
        verify_identity_fields(
            data,
            id_field="context_id",
            observed_id=result.context_id,
            observed_hash=result.artifact_hash,
        )
        return result

    @classmethod
    def from_json(cls, text: str) -> "DetectorErrorContextV1":
        document = json.loads(text)
        if not isinstance(document, dict):
            raise V6FoundationError("detector context must be a JSON object")
        return cls.from_dict(document)
