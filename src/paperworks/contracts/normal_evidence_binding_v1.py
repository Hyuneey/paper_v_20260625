"""Canonical Rule v1 identifier bindings for normal-only v6 evidence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

from paperworks.contracts.evidence_v1 import (
    EvidenceLagRangeV1,
    EvidenceSelectionPolicyV1,
)
from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    canonical_json_v1,
    reject_unknown_fields,
    require_identifier,
    require_sha256,
    require_sha256_refs,
    require_unique_strings,
    stable_hash_v1,
    verify_identity_fields,
)


NORMAL_REFERENCE_BINDING_ARTIFACT_TYPE = "normal_reference_set_binding"
RULE_EVIDENCE_BINDING_ARTIFACT_TYPE = "rule_evidence_binding"
_NREF_ID = r"^NREF-V6-[A-F0-9]{20}$"
_EVID_ID = r"^EVID-V6-[A-F0-9]{20}$"
_EDGE_ID = r"^EDGE-[A-Za-z0-9._-]+$"
_PARAMETER_ID = r"^PARAM-[A-Za-z0-9._-]+$"
REQUIRED_SUPPORTED_CLAIMS = frozenset(
    {"state_conditioned_response", "typical_lag"}
)
REQUIRED_PROHIBITED_CLAIMS = frozenset(
    {"physical_causality", "root_cause", "universal_invariant"}
)


def _canonical_upper_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = sha256(canonical_json_v1(payload).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:20].upper()}"


@dataclass(frozen=True)
class SourceIdentifierBindingV1:
    """Bind one source SHA-256 reference to one canonical identifier."""

    source_artifact_hash: str
    canonical_id: str
    canonical_artifact_hash: str

    def __post_init__(self) -> None:
        require_sha256(self.source_artifact_hash, "source_artifact_hash")
        require_identifier(self.canonical_id, "canonical_id")
        require_sha256(self.canonical_artifact_hash, "canonical_artifact_hash")
        if self.source_artifact_hash != self.canonical_artifact_hash:
            raise V6FoundationError(
                "source and canonical artifact hashes must match exactly"
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "source_artifact_hash": self.source_artifact_hash,
            "canonical_id": self.canonical_id,
            "canonical_artifact_hash": self.canonical_artifact_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SourceIdentifierBindingV1":
        reject_unknown_fields(
            data,
            frozenset(
                {
                    "source_artifact_hash",
                    "canonical_id",
                    "canonical_artifact_hash",
                }
            ),
            "source_identifier_binding",
        )
        return cls(
            source_artifact_hash=str(data["source_artifact_hash"]),
            canonical_id=str(data["canonical_id"]),
            canonical_artifact_hash=str(data["canonical_artifact_hash"]),
        )


def derive_normal_reference_id_v1(
    *,
    source_normal_reference_hashes: tuple[str, ...],
    dataset_manifest_id: str,
    data_view_id: str,
    split_manifest_id: str,
    dataset_version: str,
    process_scope: tuple[str, ...],
    subsystem: str,
    operating_regime_id: str,
    matching_policy_id: str,
    matching_policy_version: str,
    matching_method: str,
) -> str:
    """Derive the Rule v1 normal-reference ID without an evidence-hash cycle."""

    source_hashes = require_sha256_refs(
        source_normal_reference_hashes,
        "source_normal_reference_hashes",
        allow_empty=False,
    )
    for name, value in (
        ("dataset_manifest_id", dataset_manifest_id),
        ("data_view_id", data_view_id),
        ("split_manifest_id", split_manifest_id),
    ):
        require_sha256(value, name)
    scope = require_unique_strings(
        process_scope, "process_scope", allow_empty=False
    )
    payload = {
        "source_normal_reference_hashes": list(source_hashes),
        "dataset_manifest_id": dataset_manifest_id,
        "data_view_id": data_view_id,
        "split_manifest_id": split_manifest_id,
        "dataset_version": dataset_version,
        "process_scope": list(scope),
        "subsystem": subsystem,
        "operating_regime_id": operating_regime_id,
        "matching_policy_id": matching_policy_id,
        "matching_policy_version": matching_policy_version,
        "matching_method": matching_method,
    }
    return _canonical_upper_id("NREF-V6", payload)


@dataclass(frozen=True)
class NormalReferenceSetBindingV1:
    normal_relation_evidence_id: str
    normal_relation_evidence_hash: str
    source_normal_reference_hashes: tuple[str, ...]
    dataset_manifest_id: str
    data_view_id: str
    split_manifest_id: str
    dataset_version: str
    process_scope: tuple[str, ...]
    subsystem: str
    operating_regime_id: str
    matching_policy_id: str
    matching_policy_version: str
    matching_method: str
    deterministic_tie_breaking: bool
    label_performance_used: bool
    raw_values_included: bool
    creation_metadata: CreationMetadataV1
    authority_granted: bool
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = NORMAL_REFERENCE_BINDING_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported normal-reference binding schema_version"
            )
        if self.artifact_type != NORMAL_REFERENCE_BINDING_ARTIFACT_TYPE:
            raise V6FoundationError(
                "invalid normal-reference binding artifact_type"
            )
        require_identifier(
            self.normal_relation_evidence_id, "normal_relation_evidence_id"
        )
        require_sha256(
            self.normal_relation_evidence_hash,
            "normal_relation_evidence_hash",
        )
        object.__setattr__(
            self,
            "source_normal_reference_hashes",
            require_sha256_refs(
                self.source_normal_reference_hashes,
                "source_normal_reference_hashes",
                allow_empty=False,
            ),
        )
        for name, value in (
            ("dataset_manifest_id", self.dataset_manifest_id),
            ("data_view_id", self.data_view_id),
            ("split_manifest_id", self.split_manifest_id),
        ):
            require_sha256(value, name)
        object.__setattr__(
            self,
            "process_scope",
            require_unique_strings(
                self.process_scope, "process_scope", allow_empty=False
            ),
        )
        for name, value in (
            ("dataset_version", self.dataset_version),
            ("subsystem", self.subsystem),
            ("operating_regime_id", self.operating_regime_id),
            ("matching_policy_id", self.matching_policy_id),
            ("matching_policy_version", self.matching_policy_version),
            ("matching_method", self.matching_method),
        ):
            require_identifier(value, name)
        if not self.deterministic_tie_breaking:
            raise V6FoundationError(
                "normal-reference matching must use deterministic tie-breaking"
            )
        if (
            self.label_performance_used
            or self.raw_values_included
            or self.authority_granted
        ):
            raise V6FoundationError(
                "normal-reference binding cannot use labels, raw values, or grant authority"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "normal_relation_evidence_id": self.normal_relation_evidence_id,
            "normal_relation_evidence_hash": self.normal_relation_evidence_hash,
            "source_normal_reference_hashes": list(
                self.source_normal_reference_hashes
            ),
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
            "split_manifest_id": self.split_manifest_id,
            "dataset_version": self.dataset_version,
            "process_scope": list(self.process_scope),
            "subsystem": self.subsystem,
            "operating_regime_id": self.operating_regime_id,
            "matching_policy_id": self.matching_policy_id,
            "matching_policy_version": self.matching_policy_version,
            "matching_method": self.matching_method,
            "deterministic_tie_breaking": self.deterministic_tie_breaking,
            "label_performance_used": self.label_performance_used,
            "raw_values_included": self.raw_values_included,
            "creation_metadata": self.creation_metadata.to_dict(),
            "authority_granted": self.authority_granted,
        }

    @property
    def normal_reference_id(self) -> str:
        return derive_normal_reference_id_v1(
            source_normal_reference_hashes=self.source_normal_reference_hashes,
            dataset_manifest_id=self.dataset_manifest_id,
            data_view_id=self.data_view_id,
            split_manifest_id=self.split_manifest_id,
            dataset_version=self.dataset_version,
            process_scope=self.process_scope,
            subsystem=self.subsystem,
            operating_regime_id=self.operating_regime_id,
            matching_policy_id=self.matching_policy_id,
            matching_policy_version=self.matching_policy_version,
            matching_method=self.matching_method,
        )

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["normal_reference_id"] = self.normal_reference_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["normal_reference_id"] = self.normal_reference_id
        payload["artifact_hash"] = self.artifact_hash
        return payload

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> "NormalReferenceSetBindingV1":
        allowed = frozenset(
            {
                "schema_version",
                "artifact_type",
                "normal_reference_id",
                "artifact_hash",
                "normal_relation_evidence_id",
                "normal_relation_evidence_hash",
                "source_normal_reference_hashes",
                "dataset_manifest_id",
                "data_view_id",
                "split_manifest_id",
                "dataset_version",
                "process_scope",
                "subsystem",
                "operating_regime_id",
                "matching_policy_id",
                "matching_policy_version",
                "matching_method",
                "deterministic_tie_breaking",
                "label_performance_used",
                "raw_values_included",
                "creation_metadata",
                "authority_granted",
            }
        )
        reject_unknown_fields(data, allowed, NORMAL_REFERENCE_BINDING_ARTIFACT_TYPE)
        result = cls(
            normal_relation_evidence_id=str(
                data["normal_relation_evidence_id"]
            ),
            normal_relation_evidence_hash=str(
                data["normal_relation_evidence_hash"]
            ),
            source_normal_reference_hashes=tuple(
                str(item) for item in data["source_normal_reference_hashes"]
            ),
            dataset_manifest_id=str(data["dataset_manifest_id"]),
            data_view_id=str(data["data_view_id"]),
            split_manifest_id=str(data["split_manifest_id"]),
            dataset_version=str(data["dataset_version"]),
            process_scope=tuple(str(item) for item in data["process_scope"]),
            subsystem=str(data["subsystem"]),
            operating_regime_id=str(data["operating_regime_id"]),
            matching_policy_id=str(data["matching_policy_id"]),
            matching_policy_version=str(data["matching_policy_version"]),
            matching_method=str(data["matching_method"]),
            deterministic_tie_breaking=(
                data["deterministic_tie_breaking"] is True
            ),
            label_performance_used=data["label_performance_used"] is True,
            raw_values_included=data["raw_values_included"] is True,
            creation_metadata=CreationMetadataV1.from_dict(
                data["creation_metadata"]
            ),
            authority_granted=data["authority_granted"] is True,
            schema_version=str(
                data.get("schema_version", V6_FOUNDATION_SCHEMA_VERSION)
            ),
            artifact_type=str(
                data.get(
                    "artifact_type", NORMAL_REFERENCE_BINDING_ARTIFACT_TYPE
                )
            ),
        )
        supplied_id = data.get("normal_reference_id")
        if supplied_id is not None and (
            not isinstance(supplied_id, str)
            or re.fullmatch(_NREF_ID, supplied_id) is None
            or supplied_id != result.normal_reference_id
        ):
            raise V6FoundationError(
                "normal_reference_id does not match the binding content"
            )
        verify_identity_fields(
            data,
            id_field="normal_reference_id",
            observed_id=result.normal_reference_id,
            observed_hash=result.artifact_hash,
        )
        return result


@dataclass(frozen=True)
class RuleEvidenceBindingV1:
    normal_relation_evidence_id: str
    normal_relation_evidence_hash: str
    dataset_manifest_id: str
    data_view_id: str
    split_manifest_id: str
    dataset_version: str
    process_scope: tuple[str, ...]
    subsystem: str
    source_variables: tuple[str, ...]
    target_variables: tuple[str, ...]
    operating_regime_id: str
    operating_regime_condition_bindings: tuple[
        SourceIdentifierBindingV1, ...
    ]
    graph_edge_refs: tuple[str, ...]
    graph_edge_source_bindings: tuple[SourceIdentifierBindingV1, ...]
    normal_reference_binding_ref: str
    normal_reference_binding_hash: str
    parameter_artifact_refs: tuple[str, ...]
    parameter_source_bindings: tuple[SourceIdentifierBindingV1, ...]
    candidate_lag_range: EvidenceLagRangeV1
    supported_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    selection_policy: EvidenceSelectionPolicyV1
    data_split: str
    raw_values_included: bool
    label_performance_used: bool
    detector_context_used: bool
    creation_metadata: CreationMetadataV1
    validity_authority_granted: bool
    runtime_authority_granted: bool
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = RULE_EVIDENCE_BINDING_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise V6FoundationError(
                "unsupported rule-evidence binding schema_version"
            )
        if self.artifact_type != RULE_EVIDENCE_BINDING_ARTIFACT_TYPE:
            raise V6FoundationError("invalid rule-evidence binding artifact_type")
        require_identifier(
            self.normal_relation_evidence_id, "normal_relation_evidence_id"
        )
        require_sha256(
            self.normal_relation_evidence_hash,
            "normal_relation_evidence_hash",
        )
        for name, value in (
            ("dataset_manifest_id", self.dataset_manifest_id),
            ("data_view_id", self.data_view_id),
            ("split_manifest_id", self.split_manifest_id),
            ("normal_reference_binding_hash", self.normal_reference_binding_hash),
        ):
            require_sha256(value, name)
        object.__setattr__(
            self,
            "process_scope",
            require_unique_strings(
                self.process_scope, "process_scope", allow_empty=False
            ),
        )
        object.__setattr__(
            self,
            "source_variables",
            require_unique_strings(
                self.source_variables, "source_variables", allow_empty=False
            ),
        )
        object.__setattr__(
            self,
            "target_variables",
            require_unique_strings(
                self.target_variables, "target_variables", allow_empty=False
            ),
        )
        if len(self.source_variables) != 1 or len(self.target_variables) != 1:
            raise V6FoundationError(
                "first canonical bridge requires one source and one target"
            )
        if self.source_variables[0] == self.target_variables[0]:
            raise V6FoundationError("source and target variables must differ")
        for name, value in (
            ("dataset_version", self.dataset_version),
            ("subsystem", self.subsystem),
            ("operating_regime_id", self.operating_regime_id),
        ):
            require_identifier(value, name)
        condition_ids = tuple(
            item.canonical_id
            for item in self.operating_regime_condition_bindings
        )
        require_unique_strings(condition_ids, "operating_regime_condition_ids")
        object.__setattr__(
            self,
            "graph_edge_refs",
            require_unique_strings(
                self.graph_edge_refs, "graph_edge_refs", allow_empty=False
            ),
        )
        if (
            len(self.graph_edge_refs) != 1
            or re.fullmatch(_EDGE_ID, self.graph_edge_refs[0]) is None
        ):
            raise V6FoundationError(
                "first canonical bridge requires one canonical EDGE reference"
            )
        if tuple(
            item.canonical_id for item in self.graph_edge_source_bindings
        ) != self.graph_edge_refs:
            raise V6FoundationError(
                "graph edge source bindings must match graph_edge_refs"
            )
        if re.fullmatch(_NREF_ID, self.normal_reference_binding_ref) is None:
            raise V6FoundationError(
                "normal_reference_binding_ref must be a NREF-V6 identifier"
            )
        object.__setattr__(
            self,
            "parameter_artifact_refs",
            require_unique_strings(
                self.parameter_artifact_refs,
                "parameter_artifact_refs",
                allow_empty=False,
            ),
        )
        if any(
            re.fullmatch(_PARAMETER_ID, item) is None
            for item in self.parameter_artifact_refs
        ):
            raise V6FoundationError(
                "parameter_artifact_refs must contain canonical PARAM identifiers"
            )
        source_parameter_ids = tuple(
            item.canonical_id for item in self.parameter_source_bindings
        )
        if not set(source_parameter_ids).issubset(self.parameter_artifact_refs):
            raise V6FoundationError(
                "parameter source bindings must resolve inside parameter_artifact_refs"
            )
        if (
            self.candidate_lag_range.minimum
            > self.candidate_lag_range.maximum
        ):
            raise V6FoundationError("candidate lag range is inverted")
        object.__setattr__(
            self,
            "supported_claims",
            require_unique_strings(
                self.supported_claims, "supported_claims", allow_empty=False
            ),
        )
        object.__setattr__(
            self,
            "prohibited_claims",
            require_unique_strings(
                self.prohibited_claims,
                "prohibited_claims",
                allow_empty=False,
            ),
        )
        if not REQUIRED_SUPPORTED_CLAIMS.issubset(self.supported_claims):
            raise V6FoundationError(
                "rule evidence binding lacks required delayed-response claims"
            )
        if not REQUIRED_PROHIBITED_CLAIMS.issubset(self.prohibited_claims):
            raise V6FoundationError(
                "rule evidence binding claim boundary is incomplete"
            )
        policy = self.selection_policy
        if (
            not policy.pre_registered
            or not policy.deterministic_tie_breaking
            or policy.label_performance_used
        ):
            raise V6FoundationError(
                "rule evidence selection policy must be deterministic and label-free"
            )
        if self.data_split != "normal_relation_calibration":
            raise V6FoundationError(
                "v6 rule evidence requires normal_relation_calibration"
            )
        if (
            self.raw_values_included
            or self.label_performance_used
            or self.detector_context_used
            or self.validity_authority_granted
            or self.runtime_authority_granted
        ):
            raise V6FoundationError(
                "rule evidence binding violates data or authority boundaries"
            )

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "normal_relation_evidence_id": self.normal_relation_evidence_id,
            "normal_relation_evidence_hash": self.normal_relation_evidence_hash,
            "dataset_manifest_id": self.dataset_manifest_id,
            "data_view_id": self.data_view_id,
            "split_manifest_id": self.split_manifest_id,
            "dataset_version": self.dataset_version,
            "process_scope": list(self.process_scope),
            "subsystem": self.subsystem,
            "source_variables": list(self.source_variables),
            "target_variables": list(self.target_variables),
            "operating_regime_id": self.operating_regime_id,
            "operating_regime_condition_bindings": [
                item.to_dict()
                for item in self.operating_regime_condition_bindings
            ],
            "graph_edge_refs": list(self.graph_edge_refs),
            "graph_edge_source_bindings": [
                item.to_dict() for item in self.graph_edge_source_bindings
            ],
            "normal_reference_binding_ref": self.normal_reference_binding_ref,
            "normal_reference_binding_hash": self.normal_reference_binding_hash,
            "parameter_artifact_refs": list(self.parameter_artifact_refs),
            "parameter_source_bindings": [
                item.to_dict() for item in self.parameter_source_bindings
            ],
            "candidate_lag_range": {
                "minimum": self.candidate_lag_range.minimum,
                "maximum": self.candidate_lag_range.maximum,
                "unit": self.candidate_lag_range.unit,
            },
            "supported_claims": list(self.supported_claims),
            "prohibited_claims": list(self.prohibited_claims),
            "selection_policy": {
                "policy_id": self.selection_policy.policy_id,
                "policy_version": self.selection_policy.policy_version,
                "regime_match_required": (
                    self.selection_policy.regime_match_required
                ),
                "subsystem_match_required": (
                    self.selection_policy.subsystem_match_required
                ),
                "label_performance_used": (
                    self.selection_policy.label_performance_used
                ),
                "deterministic_tie_breaking": (
                    self.selection_policy.deterministic_tie_breaking
                ),
                "pre_registered": self.selection_policy.pre_registered,
            },
            "data_split": self.data_split,
            "raw_values_included": self.raw_values_included,
            "label_performance_used": self.label_performance_used,
            "detector_context_used": self.detector_context_used,
            "creation_metadata": self.creation_metadata.to_dict(),
            "validity_authority_granted": self.validity_authority_granted,
            "runtime_authority_granted": self.runtime_authority_granted,
        }

    @property
    def evidence_id(self) -> str:
        return _canonical_upper_id("EVID-V6", self._content_dict())

    @property
    def artifact_hash(self) -> str:
        payload = self._content_dict()
        payload["evidence_id"] = self.evidence_id
        return stable_hash_v1(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = self._content_dict()
        payload["evidence_id"] = self.evidence_id
        payload["artifact_hash"] = self.artifact_hash
        return payload

    def to_json(self) -> str:
        return canonical_json_v1(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RuleEvidenceBindingV1":
        allowed = frozenset(
            {
                "schema_version",
                "artifact_type",
                "evidence_id",
                "artifact_hash",
                "normal_relation_evidence_id",
                "normal_relation_evidence_hash",
                "dataset_manifest_id",
                "data_view_id",
                "split_manifest_id",
                "dataset_version",
                "process_scope",
                "subsystem",
                "source_variables",
                "target_variables",
                "operating_regime_id",
                "operating_regime_condition_bindings",
                "graph_edge_refs",
                "graph_edge_source_bindings",
                "normal_reference_binding_ref",
                "normal_reference_binding_hash",
                "parameter_artifact_refs",
                "parameter_source_bindings",
                "candidate_lag_range",
                "supported_claims",
                "prohibited_claims",
                "selection_policy",
                "data_split",
                "raw_values_included",
                "label_performance_used",
                "detector_context_used",
                "creation_metadata",
                "validity_authority_granted",
                "runtime_authority_granted",
            }
        )
        reject_unknown_fields(data, allowed, RULE_EVIDENCE_BINDING_ARTIFACT_TYPE)
        lag = data["candidate_lag_range"]
        policy = data["selection_policy"]
        result = cls(
            normal_relation_evidence_id=str(
                data["normal_relation_evidence_id"]
            ),
            normal_relation_evidence_hash=str(
                data["normal_relation_evidence_hash"]
            ),
            dataset_manifest_id=str(data["dataset_manifest_id"]),
            data_view_id=str(data["data_view_id"]),
            split_manifest_id=str(data["split_manifest_id"]),
            dataset_version=str(data["dataset_version"]),
            process_scope=tuple(str(item) for item in data["process_scope"]),
            subsystem=str(data["subsystem"]),
            source_variables=tuple(
                str(item) for item in data["source_variables"]
            ),
            target_variables=tuple(
                str(item) for item in data["target_variables"]
            ),
            operating_regime_id=str(data["operating_regime_id"]),
            operating_regime_condition_bindings=tuple(
                SourceIdentifierBindingV1.from_dict(item)
                for item in data["operating_regime_condition_bindings"]
            ),
            graph_edge_refs=tuple(
                str(item) for item in data["graph_edge_refs"]
            ),
            graph_edge_source_bindings=tuple(
                SourceIdentifierBindingV1.from_dict(item)
                for item in data["graph_edge_source_bindings"]
            ),
            normal_reference_binding_ref=str(
                data["normal_reference_binding_ref"]
            ),
            normal_reference_binding_hash=str(
                data["normal_reference_binding_hash"]
            ),
            parameter_artifact_refs=tuple(
                str(item) for item in data["parameter_artifact_refs"]
            ),
            parameter_source_bindings=tuple(
                SourceIdentifierBindingV1.from_dict(item)
                for item in data["parameter_source_bindings"]
            ),
            candidate_lag_range=EvidenceLagRangeV1(
                lag["minimum"], lag["maximum"], str(lag["unit"])
            ),
            supported_claims=tuple(
                str(item) for item in data["supported_claims"]
            ),
            prohibited_claims=tuple(
                str(item) for item in data["prohibited_claims"]
            ),
            selection_policy=EvidenceSelectionPolicyV1(
                policy_id=str(policy["policy_id"]),
                policy_version=str(policy["policy_version"]),
                regime_match_required=policy["regime_match_required"] is True,
                subsystem_match_required=(
                    policy["subsystem_match_required"] is True
                ),
                label_performance_used=(
                    policy["label_performance_used"] is True
                ),
                deterministic_tie_breaking=(
                    policy["deterministic_tie_breaking"] is True
                ),
                pre_registered=policy["pre_registered"] is True,
            ),
            data_split=str(data["data_split"]),
            raw_values_included=data["raw_values_included"] is True,
            label_performance_used=data["label_performance_used"] is True,
            detector_context_used=data["detector_context_used"] is True,
            creation_metadata=CreationMetadataV1.from_dict(
                data["creation_metadata"]
            ),
            validity_authority_granted=(
                data["validity_authority_granted"] is True
            ),
            runtime_authority_granted=(
                data["runtime_authority_granted"] is True
            ),
            schema_version=str(
                data.get("schema_version", V6_FOUNDATION_SCHEMA_VERSION)
            ),
            artifact_type=str(
                data.get("artifact_type", RULE_EVIDENCE_BINDING_ARTIFACT_TYPE)
            ),
        )
        supplied_id = data.get("evidence_id")
        if supplied_id is not None and (
            not isinstance(supplied_id, str)
            or re.fullmatch(_EVID_ID, supplied_id) is None
        ):
            raise V6FoundationError("evidence_id is not a canonical EVID-V6 ID")
        verify_identity_fields(
            data,
            id_field="evidence_id",
            observed_id=result.evidence_id,
            observed_hash=result.artifact_hash,
        )
        return result

    @classmethod
    def from_json(cls, text: str) -> "RuleEvidenceBindingV1":
        document = json.loads(text)
        if not isinstance(document, dict):
            raise V6FoundationError(
                "rule evidence binding must be a JSON object"
            )
        return cls.from_dict(document)
