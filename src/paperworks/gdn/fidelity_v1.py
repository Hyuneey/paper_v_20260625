"""Versioned, non-authorizing GDN source-fidelity records."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    parse_iso_datetime,
    require_identifier,
    require_sha256,
    require_unique_strings,
    stable_hash_v1,
    verify_identity_fields,
)


GDN_BACKEND_FIDELITY_ARTIFACT_TYPE = "gdn_backend_fidelity_record"
GDN_FIDELITY_FREEZE_ARTIFACT_TYPE = "gdn_fidelity_freeze"
PINNED_GDN_REPOSITORY = "https://github.com/d-ailin/GDN"
PINNED_GDN_COMMIT = "9853899da860682669a134e4af315d036aab4eca"
REQUIRED_RQ1_FIDELITY_CLASS = "upstream_aligned_validated"
_GIT_OBJECT_PATTERN = re.compile(r"^[a-f0-9]{40}$")


class GDNFidelityError(ValueError):
    """Raised when a GDN fidelity record violates its claim boundary."""


class GDNFidelityClassV1(str, Enum):
    PROJECT_OWNED_EXTRACTION_COMPONENT = "project_owned_extraction_component"
    SYNTHETIC_SMOKE_ONLY = "synthetic_smoke_only"
    UPSTREAM_ALIGNED_UNVERIFIED = "upstream_aligned_unverified"
    UPSTREAM_ALIGNED_VALIDATED = "upstream_aligned_validated"


@dataclass(frozen=True)
class UpstreamFileRecordV1:
    path: str
    git_blob_sha: str
    sha256: str

    def __post_init__(self) -> None:
        if (
            not self.path
            or self.path.startswith(("/", "\\"))
            or ".." in self.path.replace("\\", "/").split("/")
        ):
            raise GDNFidelityError("upstream path must be safe and relative")
        if _GIT_OBJECT_PATTERN.fullmatch(self.git_blob_sha) is None:
            raise GDNFidelityError("git_blob_sha must be a full Git object ID")
        require_sha256(self.sha256, "upstream file sha256")

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "git_blob_sha": self.git_blob_sha,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "UpstreamFileRecordV1":
        return cls(
            path=str(data["path"]),
            git_blob_sha=str(data["git_blob_sha"]),
            sha256=str(data["sha256"]),
        )


@dataclass(frozen=True)
class GDNBackendFidelityRecordV1:
    backend_id: str
    backend_version: str
    implementation_module: str
    implementation_symbols: tuple[str, ...]
    implementation_behavior_hash: str
    fidelity_class: GDNFidelityClassV1
    scientific_gdn_claim_allowed: bool
    production_candidate_ranking_allowed: bool
    upstream_repository: str
    upstream_commit: str
    upstream_file_records: tuple[UpstreamFileRecordV1, ...]
    mapped_upstream_features: tuple[str, ...]
    missing_upstream_features: tuple[str, ...]
    intentional_project_deviations: tuple[str, ...]
    input_contract: str
    training_objective: str
    learned_graph_behavior: str
    candidate_mask_policy: str
    self_edge_policy: str
    split_policy: str
    dependency_requirements: tuple[str, ...]
    data_accessed: bool
    model_trained: bool
    created_at: str
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = GDN_BACKEND_FIDELITY_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if isinstance(self.fidelity_class, str):
            object.__setattr__(
                self, "fidelity_class", GDNFidelityClassV1(self.fidelity_class)
            )
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise GDNFidelityError("unsupported GDN fidelity schema version")
        if self.artifact_type != GDN_BACKEND_FIDELITY_ARTIFACT_TYPE:
            raise GDNFidelityError("invalid GDN fidelity artifact type")
        require_identifier(self.backend_id, "backend_id")
        require_identifier(self.backend_version, "backend_version")
        require_identifier(self.implementation_module, "implementation_module")
        object.__setattr__(
            self,
            "implementation_symbols",
            require_unique_strings(
                self.implementation_symbols,
                "implementation_symbols",
                allow_empty=False,
            ),
        )
        require_sha256(
            self.implementation_behavior_hash, "implementation_behavior_hash"
        )
        if self.upstream_repository != PINNED_GDN_REPOSITORY:
            raise GDNFidelityError("upstream repository must match the pinned GDN source")
        if self.upstream_commit != PINNED_GDN_COMMIT:
            raise GDNFidelityError("upstream commit must match the pinned GDN source")
        if not self.upstream_file_records:
            raise GDNFidelityError("at least one upstream file record is required")
        paths = tuple(record.path for record in self.upstream_file_records)
        if len(paths) != len(set(paths)):
            raise GDNFidelityError("upstream file paths must be unique")
        for field_name in (
            "mapped_upstream_features",
            "missing_upstream_features",
            "intentional_project_deviations",
            "dependency_requirements",
        ):
            object.__setattr__(
                self,
                field_name,
                require_unique_strings(
                    getattr(self, field_name), field_name, allow_empty=False
                ),
            )
        for field_name in (
            "input_contract",
            "training_objective",
            "learned_graph_behavior",
            "candidate_mask_policy",
            "self_edge_policy",
            "split_policy",
        ):
            if not getattr(self, field_name):
                raise GDNFidelityError(f"{field_name} is required")
        parse_iso_datetime(self.created_at, "created_at")
        if self.scientific_gdn_claim_allowed and (
            self.fidelity_class
            is not GDNFidelityClassV1.UPSTREAM_ALIGNED_VALIDATED
        ):
            raise GDNFidelityError(
                "scientific GDN claims require upstream_aligned_validated"
            )
        if self.production_candidate_ranking_allowed and (
            self.fidelity_class
            is not GDNFidelityClassV1.UPSTREAM_ALIGNED_VALIDATED
        ):
            raise GDNFidelityError(
                "production candidate ranking requires upstream_aligned_validated"
            )

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "backend_id": self.backend_id,
            "backend_version": self.backend_version,
            "implementation_module": self.implementation_module,
            "implementation_symbols": list(self.implementation_symbols),
            "implementation_behavior_hash": self.implementation_behavior_hash,
            "fidelity_class": self.fidelity_class.value,
            "scientific_gdn_claim_allowed": self.scientific_gdn_claim_allowed,
            "production_candidate_ranking_allowed": (
                self.production_candidate_ranking_allowed
            ),
            "upstream_repository": self.upstream_repository,
            "upstream_commit": self.upstream_commit,
            "upstream_file_records": [
                record.to_dict() for record in self.upstream_file_records
            ],
            "mapped_upstream_features": list(self.mapped_upstream_features),
            "missing_upstream_features": list(self.missing_upstream_features),
            "intentional_project_deviations": list(
                self.intentional_project_deviations
            ),
            "input_contract": self.input_contract,
            "training_objective": self.training_objective,
            "learned_graph_behavior": self.learned_graph_behavior,
            "candidate_mask_policy": self.candidate_mask_policy,
            "self_edge_policy": self.self_edge_policy,
            "split_policy": self.split_policy,
            "dependency_requirements": list(self.dependency_requirements),
            "data_accessed": self.data_accessed,
            "model_trained": self.model_trained,
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any]
    ) -> "GDNBackendFidelityRecordV1":
        result = cls(
            backend_id=str(data["backend_id"]),
            backend_version=str(data["backend_version"]),
            implementation_module=str(data["implementation_module"]),
            implementation_symbols=tuple(data["implementation_symbols"]),
            implementation_behavior_hash=str(data["implementation_behavior_hash"]),
            fidelity_class=GDNFidelityClassV1(str(data["fidelity_class"])),
            scientific_gdn_claim_allowed=bool(
                data["scientific_gdn_claim_allowed"]
            ),
            production_candidate_ranking_allowed=bool(
                data["production_candidate_ranking_allowed"]
            ),
            upstream_repository=str(data["upstream_repository"]),
            upstream_commit=str(data["upstream_commit"]),
            upstream_file_records=tuple(
                UpstreamFileRecordV1.from_dict(item)
                for item in data["upstream_file_records"]
            ),
            mapped_upstream_features=tuple(data["mapped_upstream_features"]),
            missing_upstream_features=tuple(data["missing_upstream_features"]),
            intentional_project_deviations=tuple(
                data["intentional_project_deviations"]
            ),
            input_contract=str(data["input_contract"]),
            training_objective=str(data["training_objective"]),
            learned_graph_behavior=str(data["learned_graph_behavior"]),
            candidate_mask_policy=str(data["candidate_mask_policy"]),
            self_edge_policy=str(data["self_edge_policy"]),
            split_policy=str(data["split_policy"]),
            dependency_requirements=tuple(data["dependency_requirements"]),
            data_accessed=bool(data["data_accessed"]),
            model_trained=bool(data["model_trained"]),
            created_at=str(data["created_at"]),
            schema_version=str(data["schema_version"]),
            artifact_type=str(data["artifact_type"]),
        )
        verify_identity_fields(
            data,
            id_field="backend_id",
            observed_id=result.backend_id,
            observed_hash=result.artifact_hash,
        )
        return result


@dataclass(frozen=True)
class GDNFidelityFreezeV1:
    task_id: str
    status: str
    upstream_repository: str
    upstream_commit: str
    upstream_license: str
    upstream_license_blob_sha: str
    upstream_license_sha256: str
    upstream_file_records: tuple[UpstreamFileRecordV1, ...]
    backend_records: tuple[GDNBackendFidelityRecordV1, ...]
    required_rq1_fidelity_class: str
    production_backend_decision: str
    future_backend_options: tuple[str, ...]
    data_accessed: bool
    model_trained: bool
    created_at: str
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = GDN_FIDELITY_FREEZE_ARTIFACT_TYPE

    def __post_init__(self) -> None:
        if self.task_id != "TASK-039P1D":
            raise GDNFidelityError("fidelity freeze task_id must be TASK-039P1D")
        if self.status != "passed_gdn_optional_import_and_fidelity_freeze":
            raise GDNFidelityError("invalid TASK-039P1D freeze status")
        if self.schema_version != V6_FOUNDATION_SCHEMA_VERSION:
            raise GDNFidelityError("unsupported fidelity-freeze schema version")
        if self.artifact_type != GDN_FIDELITY_FREEZE_ARTIFACT_TYPE:
            raise GDNFidelityError("invalid fidelity-freeze artifact type")
        if self.upstream_repository != PINNED_GDN_REPOSITORY:
            raise GDNFidelityError("fidelity freeze repository mismatch")
        if self.upstream_commit != PINNED_GDN_COMMIT:
            raise GDNFidelityError("fidelity freeze commit mismatch")
        if self.upstream_license != "MIT":
            raise GDNFidelityError("pinned GDN license must be MIT")
        if _GIT_OBJECT_PATTERN.fullmatch(self.upstream_license_blob_sha) is None:
            raise GDNFidelityError("license blob SHA must be a full Git object ID")
        require_sha256(self.upstream_license_sha256, "upstream_license_sha256")
        if len(self.upstream_file_records) < 7:
            raise GDNFidelityError("all required upstream GDN files must be frozen")
        expected_backends = {
            "deterministic_embedding_smoke",
            "torch_pyg_cpu_smoke",
            "masked_candidate_extraction",
        }
        observed_backends = {record.backend_id for record in self.backend_records}
        if observed_backends != expected_backends:
            raise GDNFidelityError("exactly three TASK-039P1D backends are required")
        if len(observed_backends) != len(self.backend_records):
            raise GDNFidelityError("backend IDs must be unique")
        if any(
            record.fidelity_class
            is GDNFidelityClassV1.UPSTREAM_ALIGNED_VALIDATED
            for record in self.backend_records
        ):
            raise GDNFidelityError(
                "TASK-039P1D cannot create an upstream_aligned_validated record"
            )
        if self.required_rq1_fidelity_class != REQUIRED_RQ1_FIDELITY_CLASS:
            raise GDNFidelityError("RQ1 fidelity threshold must remain fail-closed")
        if self.production_backend_decision != "pending_TASK039A_B_feasibility":
            raise GDNFidelityError("production backend decision must remain pending")
        object.__setattr__(
            self,
            "future_backend_options",
            require_unique_strings(
                self.future_backend_options,
                "future_backend_options",
                allow_empty=False,
            ),
        )
        if self.data_accessed or self.model_trained:
            raise GDNFidelityError("TASK-039P1D is a no-data, no-training freeze")
        parse_iso_datetime(self.created_at, "created_at")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._payload())

    @property
    def record_by_backend_id(self) -> Mapping[str, GDNBackendFidelityRecordV1]:
        return {record.backend_id: record for record in self.backend_records}

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "task_id": self.task_id,
            "status": self.status,
            "upstream_repository": self.upstream_repository,
            "upstream_commit": self.upstream_commit,
            "upstream_license": self.upstream_license,
            "upstream_license_blob_sha": self.upstream_license_blob_sha,
            "upstream_license_sha256": self.upstream_license_sha256,
            "upstream_file_records": [
                record.to_dict() for record in self.upstream_file_records
            ],
            "backend_records": [record.to_dict() for record in self.backend_records],
            "required_rq1_fidelity_class": self.required_rq1_fidelity_class,
            "production_backend_decision": self.production_backend_decision,
            "future_backend_options": list(self.future_backend_options),
            "data_accessed": self.data_accessed,
            "model_trained": self.model_trained,
            "created_at": self.created_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "artifact_hash": self.artifact_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GDNFidelityFreezeV1":
        result = cls(
            task_id=str(data["task_id"]),
            status=str(data["status"]),
            upstream_repository=str(data["upstream_repository"]),
            upstream_commit=str(data["upstream_commit"]),
            upstream_license=str(data["upstream_license"]),
            upstream_license_blob_sha=str(data["upstream_license_blob_sha"]),
            upstream_license_sha256=str(data["upstream_license_sha256"]),
            upstream_file_records=tuple(
                UpstreamFileRecordV1.from_dict(item)
                for item in data["upstream_file_records"]
            ),
            backend_records=tuple(
                GDNBackendFidelityRecordV1.from_dict(item)
                for item in data["backend_records"]
            ),
            required_rq1_fidelity_class=str(data["required_rq1_fidelity_class"]),
            production_backend_decision=str(data["production_backend_decision"]),
            future_backend_options=tuple(data["future_backend_options"]),
            data_accessed=bool(data["data_accessed"]),
            model_trained=bool(data["model_trained"]),
            created_at=str(data["created_at"]),
            schema_version=str(data["schema_version"]),
            artifact_type=str(data["artifact_type"]),
        )
        supplied_hash = data.get("artifact_hash")
        if supplied_hash is not None and supplied_hash != result.artifact_hash:
            raise GDNFidelityError("fidelity-freeze artifact_hash mismatch")
        return result


__all__ = [
    "GDNBackendFidelityRecordV1",
    "GDNFidelityClassV1",
    "GDNFidelityError",
    "GDNFidelityFreezeV1",
    "PINNED_GDN_COMMIT",
    "PINNED_GDN_REPOSITORY",
    "REQUIRED_RQ1_FIDELITY_CLASS",
    "UpstreamFileRecordV1",
]
