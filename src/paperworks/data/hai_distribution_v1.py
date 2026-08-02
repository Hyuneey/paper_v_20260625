"""Official-distribution metadata and byte-equivalence contracts for HAI 23.05.

The Git snapshot and Git-LFS pointers remain the identity authority.  This
module records whether selectively downloaded files from the official Kaggle
distribution are byte-for-byte equal to those pinned objects.  It contains no
scientific data analysis and never persists response URLs or credentials.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence


HAI_DISTRIBUTION_SCHEMA_VERSION = "1.0.0"
KAGGLE_API_VERSION = "v1"
KAGGLE_CLIENT_NAME = "paperworks_stdlib_urllib"
KAGGLE_CLIENT_VERSION = "1.0.0"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_COMMIT = re.compile(r"^[a-f0-9]{40}$")
_SAFE_STATUSES = frozenset(
    {
        "passed_official_distribution_byte_equivalence",
        "failed_official_distribution_byte_equivalence",
        "blocked_selective_official_download_unavailable",
    }
)


class HAIDistributionError(ValueError):
    """Raised when an official-distribution contract fails closed."""


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_self_hash(value: Mapping[str, Any], field_name: str) -> str:
    payload = dict(value)
    payload.pop(field_name, None)
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _artifact_dict(content: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(content)
    result["artifact_hash"] = sha256(
        _canonical_json(content).encode("utf-8")
    ).hexdigest()
    return result


def _verify_artifact_hash(data: Mapping[str, Any], content: Mapping[str, Any]) -> None:
    supplied = data.get("artifact_hash")
    observed = sha256(_canonical_json(content).encode("utf-8")).hexdigest()
    if supplied != observed:
        raise HAIDistributionError("artifact_hash does not match content")


def _require_sha256(value: str, field_name: str) -> str:
    if _SHA256.fullmatch(value) is None:
        raise HAIDistributionError(f"{field_name} must be a lowercase SHA-256")
    return value


def _require_commit(value: str, field_name: str) -> str:
    if _COMMIT.fullmatch(value) is None:
        raise HAIDistributionError(f"{field_name} must be a full Git commit")
    return value


def _require_iso8601(value: str, field_name: str) -> str:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HAIDistributionError(f"{field_name} must be ISO 8601") from exc
    return value


def require_safe_inventory_name(value: str) -> str:
    if not value or "\\" in value or re.match(r"^[A-Za-z]:", value):
        raise HAIDistributionError("inventory name must be a POSIX relative path")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise HAIDistributionError("inventory name escapes its relative root")
    return value


@dataclass(frozen=True)
class KaggleDistributionFileV1:
    name: str
    advertised_size_bytes: int
    creation_date: str
    file_type: str

    def __post_init__(self) -> None:
        require_safe_inventory_name(self.name)
        if self.advertised_size_bytes < 0:
            raise HAIDistributionError("advertised file size must be non-negative")
        _require_iso8601(self.creation_date, "creation_date")
        if not self.file_type:
            raise HAIDistributionError("file_type must be explicit")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "advertised_size_bytes": self.advertised_size_bytes,
            "creation_date": self.creation_date,
            "file_type": self.file_type,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "KaggleDistributionFileV1":
        return cls(
            name=str(data["name"]),
            advertised_size_bytes=int(data["advertised_size_bytes"]),
            creation_date=str(data["creation_date"]),
            file_type=str(data["file_type"]),
        )


@dataclass(frozen=True)
class HAIOfficialDistributionMetadataV1:
    task_id: str
    owner: str
    slug: str
    dataset_ref: str
    dataset_version_identifier: int
    version_timestamp: str
    license_name: str
    complete_file_inventory: tuple[KaggleDistributionFileV1, ...]
    complete_file_inventory_count: int
    official_git_repository: str
    official_git_snapshot_commit: str
    introduction_commit: str
    task039a_expected_config_hash: str
    kaggle_client_name: str
    kaggle_client_version: str
    kaggle_api_version: str
    metadata_endpoint: str
    file_inventory_endpoint: str
    selective_download_endpoint_template: str
    complete_inventory_frozen: bool
    credentials_included: bool
    signed_urls_included: bool
    created_at: str
    execution_code_commit: str
    schema_version: str = HAI_DISTRIBUTION_SCHEMA_VERSION
    artifact_type: str = "hai_official_distribution_metadata"

    def __post_init__(self) -> None:
        if self.task_id != "TASK-039AR":
            raise HAIDistributionError("distribution metadata task_id must be TASK-039AR")
        if self.owner != "icsdataset" or self.slug != "hai-security-dataset":
            raise HAIDistributionError("only the official icsdataset Kaggle source is allowed")
        if self.dataset_ref != f"{self.owner}/{self.slug}":
            raise HAIDistributionError("dataset_ref does not match owner and slug")
        if self.dataset_version_identifier <= 0:
            raise HAIDistributionError("dataset version identifier must be positive")
        _require_iso8601(self.version_timestamp, "version_timestamp")
        if self.license_name != "CC BY-SA 4.0":
            raise HAIDistributionError("Kaggle license does not match the frozen source")
        if not self.complete_file_inventory or (
            self.complete_file_inventory_count != len(self.complete_file_inventory)
        ):
            raise HAIDistributionError("complete file inventory count is inconsistent")
        names = [item.name for item in self.complete_file_inventory]
        if names != sorted(names) or len(names) != len(set(names)):
            raise HAIDistributionError("file inventory must be sorted and unique")
        if not self.complete_inventory_frozen:
            raise HAIDistributionError("metadata receipt requires a complete inventory")
        if self.credentials_included or self.signed_urls_included:
            raise HAIDistributionError("metadata receipt cannot contain credentials or URLs")
        if self.kaggle_client_name != KAGGLE_CLIENT_NAME:
            raise HAIDistributionError("unexpected Kaggle client implementation")
        if self.kaggle_client_version != KAGGLE_CLIENT_VERSION:
            raise HAIDistributionError("unexpected Kaggle client version")
        if self.kaggle_api_version != KAGGLE_API_VERSION:
            raise HAIDistributionError("unexpected Kaggle API version")
        _require_commit(self.official_git_snapshot_commit, "official_git_snapshot_commit")
        _require_commit(self.introduction_commit, "introduction_commit")
        _require_commit(self.execution_code_commit, "execution_code_commit")
        _require_sha256(self.task039a_expected_config_hash, "task039a_expected_config_hash")
        _require_iso8601(self.created_at, "created_at")
        if self.schema_version != HAI_DISTRIBUTION_SCHEMA_VERSION:
            raise HAIDistributionError("unsupported distribution metadata schema")
        if self.artifact_type != "hai_official_distribution_metadata":
            raise HAIDistributionError("invalid distribution metadata artifact type")
        allowed_prefix = "https://www.kaggle.com/api/v1/"
        for endpoint in (
            self.metadata_endpoint,
            self.file_inventory_endpoint,
            self.selective_download_endpoint_template,
        ):
            if not endpoint.startswith(allowed_prefix):
                raise HAIDistributionError("Kaggle endpoint is outside the approved API")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "task_id": self.task_id,
            "owner": self.owner,
            "slug": self.slug,
            "dataset_ref": self.dataset_ref,
            "dataset_version_identifier": self.dataset_version_identifier,
            "version_timestamp": self.version_timestamp,
            "license_name": self.license_name,
            "complete_file_inventory": [
                item.to_dict() for item in self.complete_file_inventory
            ],
            "complete_file_inventory_count": self.complete_file_inventory_count,
            "official_git_repository": self.official_git_repository,
            "official_git_snapshot_commit": self.official_git_snapshot_commit,
            "introduction_commit": self.introduction_commit,
            "task039a_expected_config_hash": self.task039a_expected_config_hash,
            "kaggle_client_name": self.kaggle_client_name,
            "kaggle_client_version": self.kaggle_client_version,
            "kaggle_api_version": self.kaggle_api_version,
            "metadata_endpoint": self.metadata_endpoint,
            "file_inventory_endpoint": self.file_inventory_endpoint,
            "selective_download_endpoint_template": self.selective_download_endpoint_template,
            "complete_inventory_frozen": self.complete_inventory_frozen,
            "credentials_included": self.credentials_included,
            "signed_urls_included": self.signed_urls_included,
            "created_at": self.created_at,
            "execution_code_commit": self.execution_code_commit,
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HAIOfficialDistributionMetadataV1":
        result = cls(
            task_id=str(data["task_id"]),
            owner=str(data["owner"]),
            slug=str(data["slug"]),
            dataset_ref=str(data["dataset_ref"]),
            dataset_version_identifier=int(data["dataset_version_identifier"]),
            version_timestamp=str(data["version_timestamp"]),
            license_name=str(data["license_name"]),
            complete_file_inventory=tuple(
                KaggleDistributionFileV1.from_dict(item)
                for item in data["complete_file_inventory"]
            ),
            complete_file_inventory_count=int(data["complete_file_inventory_count"]),
            official_git_repository=str(data["official_git_repository"]),
            official_git_snapshot_commit=str(data["official_git_snapshot_commit"]),
            introduction_commit=str(data["introduction_commit"]),
            task039a_expected_config_hash=str(data["task039a_expected_config_hash"]),
            kaggle_client_name=str(data["kaggle_client_name"]),
            kaggle_client_version=str(data["kaggle_client_version"]),
            kaggle_api_version=str(data["kaggle_api_version"]),
            metadata_endpoint=str(data["metadata_endpoint"]),
            file_inventory_endpoint=str(data["file_inventory_endpoint"]),
            selective_download_endpoint_template=str(
                data["selective_download_endpoint_template"]
            ),
            complete_inventory_frozen=data["complete_inventory_frozen"] is True,
            credentials_included=data["credentials_included"] is True,
            signed_urls_included=data["signed_urls_included"] is True,
            created_at=str(data["created_at"]),
            execution_code_commit=str(data["execution_code_commit"]),
            schema_version=str(data.get("schema_version", HAI_DISTRIBUTION_SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "hai_official_distribution_metadata")),
        )
        _verify_artifact_hash(data, result._content_dict())
        return result


@dataclass(frozen=True)
class HAIDistributionFileEquivalenceV1:
    relative_path: str
    kaggle_advertised_size_bytes: int
    official_lfs_oid_sha256: str
    official_lfs_pointer_size_bytes: int
    task039a_expected_sha256: str
    task039a_expected_size_bytes: int
    extracted_sha256: str
    extracted_size_bytes: int
    byte_equivalent: bool

    def __post_init__(self) -> None:
        require_safe_inventory_name(self.relative_path)
        if not self.relative_path.startswith("hai-23.05/"):
            raise HAIDistributionError("equivalence is limited to HAI 23.05")
        for field_name in (
            "official_lfs_oid_sha256",
            "task039a_expected_sha256",
            "extracted_sha256",
        ):
            _require_sha256(getattr(self, field_name), field_name)
        sizes = (
            self.kaggle_advertised_size_bytes,
            self.official_lfs_pointer_size_bytes,
            self.task039a_expected_size_bytes,
            self.extracted_size_bytes,
        )
        if min(sizes) < 0:
            raise HAIDistributionError("equivalence sizes must be non-negative")
        observed_equivalence = (
            len(
                {
                    self.official_lfs_oid_sha256,
                    self.task039a_expected_sha256,
                    self.extracted_sha256,
                }
            )
            == 1
            and len(set(sizes)) == 1
        )
        if self.byte_equivalent != observed_equivalence:
            raise HAIDistributionError("byte-equivalence flag is inconsistent")

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "kaggle_advertised_size_bytes": self.kaggle_advertised_size_bytes,
            "official_lfs_oid_sha256": self.official_lfs_oid_sha256,
            "official_lfs_pointer_size_bytes": self.official_lfs_pointer_size_bytes,
            "task039a_expected_sha256": self.task039a_expected_sha256,
            "task039a_expected_size_bytes": self.task039a_expected_size_bytes,
            "extracted_sha256": self.extracted_sha256,
            "extracted_size_bytes": self.extracted_size_bytes,
            "byte_equivalent": self.byte_equivalent,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HAIDistributionFileEquivalenceV1":
        return cls(
            relative_path=str(data["relative_path"]),
            kaggle_advertised_size_bytes=int(data["kaggle_advertised_size_bytes"]),
            official_lfs_oid_sha256=str(data["official_lfs_oid_sha256"]),
            official_lfs_pointer_size_bytes=int(data["official_lfs_pointer_size_bytes"]),
            task039a_expected_sha256=str(data["task039a_expected_sha256"]),
            task039a_expected_size_bytes=int(data["task039a_expected_size_bytes"]),
            extracted_sha256=str(data["extracted_sha256"]),
            extracted_size_bytes=int(data["extracted_size_bytes"]),
            byte_equivalent=data["byte_equivalent"] is True,
        )


@dataclass(frozen=True)
class HAIDistributionByteEquivalenceResultV1:
    task_id: str
    status: str
    metadata_receipt_hash: str
    execution_code_commit: str
    records: tuple[HAIDistributionFileEquivalenceV1, ...]
    expected_file_count: int
    selectively_downloaded_file_count: int
    complete_dataset_download_used: bool
    haiend_or_earlier_payload_downloaded: bool
    credentials_included: bool
    signed_urls_included: bool
    all_files_byte_equivalent: bool
    created_at: str
    schema_version: str = HAI_DISTRIBUTION_SCHEMA_VERSION
    artifact_type: str = "hai_distribution_byte_equivalence_result"

    def __post_init__(self) -> None:
        if self.task_id != "TASK-039AR" or self.status not in _SAFE_STATUSES:
            raise HAIDistributionError("invalid TASK-039AR status")
        _require_sha256(self.metadata_receipt_hash, "metadata_receipt_hash")
        _require_commit(self.execution_code_commit, "execution_code_commit")
        _require_iso8601(self.created_at, "created_at")
        names = [item.relative_path for item in self.records]
        if names != sorted(names) or len(names) != len(set(names)):
            raise HAIDistributionError("equivalence records must be sorted and unique")
        if self.expected_file_count != 10:
            raise HAIDistributionError("TASK-039AR requires exactly ten files")
        if self.selectively_downloaded_file_count != len(self.records):
            raise HAIDistributionError("selective download count is inconsistent")
        observed = len(self.records) == 10 and all(
            item.byte_equivalent for item in self.records
        )
        if self.all_files_byte_equivalent != observed:
            raise HAIDistributionError("aggregate equivalence flag is inconsistent")
        if self.status == "passed_official_distribution_byte_equivalence" and (
            not observed
            or self.complete_dataset_download_used
            or self.haiend_or_earlier_payload_downloaded
            or self.credentials_included
            or self.signed_urls_included
        ):
            raise HAIDistributionError("passing status violates the distribution boundary")
        if self.schema_version != HAI_DISTRIBUTION_SCHEMA_VERSION:
            raise HAIDistributionError("unsupported equivalence-result schema")
        if self.artifact_type != "hai_distribution_byte_equivalence_result":
            raise HAIDistributionError("invalid equivalence-result artifact type")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "task_id": self.task_id,
            "status": self.status,
            "metadata_receipt_hash": self.metadata_receipt_hash,
            "execution_code_commit": self.execution_code_commit,
            "records": [item.to_dict() for item in self.records],
            "expected_file_count": self.expected_file_count,
            "selectively_downloaded_file_count": self.selectively_downloaded_file_count,
            "complete_dataset_download_used": self.complete_dataset_download_used,
            "haiend_or_earlier_payload_downloaded": self.haiend_or_earlier_payload_downloaded,
            "credentials_included": self.credentials_included,
            "signed_urls_included": self.signed_urls_included,
            "all_files_byte_equivalent": self.all_files_byte_equivalent,
            "created_at": self.created_at,
        }

    @property
    def artifact_hash(self) -> str:
        return _artifact_dict(self._content_dict())["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return _artifact_dict(self._content_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HAIDistributionByteEquivalenceResultV1":
        result = cls(
            task_id=str(data["task_id"]),
            status=str(data["status"]),
            metadata_receipt_hash=str(data["metadata_receipt_hash"]),
            execution_code_commit=str(data["execution_code_commit"]),
            records=tuple(
                HAIDistributionFileEquivalenceV1.from_dict(item)
                for item in data["records"]
            ),
            expected_file_count=int(data["expected_file_count"]),
            selectively_downloaded_file_count=int(
                data["selectively_downloaded_file_count"]
            ),
            complete_dataset_download_used=data["complete_dataset_download_used"] is True,
            haiend_or_earlier_payload_downloaded=(
                data["haiend_or_earlier_payload_downloaded"] is True
            ),
            credentials_included=data["credentials_included"] is True,
            signed_urls_included=data["signed_urls_included"] is True,
            all_files_byte_equivalent=data["all_files_byte_equivalent"] is True,
            created_at=str(data["created_at"]),
            schema_version=str(data.get("schema_version", HAI_DISTRIBUTION_SCHEMA_VERSION)),
            artifact_type=str(
                data.get("artifact_type", "hai_distribution_byte_equivalence_result")
            ),
        )
        _verify_artifact_hash(data, result._content_dict())
        return result


def build_official_distribution_metadata(
    *,
    dataset_view: Mapping[str, Any],
    file_list: Mapping[str, Any],
    owner: str,
    slug: str,
    dataset_version_identifier: int,
    expected_files: Sequence[Mapping[str, Any]],
    official_git_repository: str,
    official_git_snapshot_commit: str,
    introduction_commit: str,
    task039a_expected_config_hash: str,
    metadata_endpoint: str,
    file_inventory_endpoint: str,
    selective_download_endpoint_template: str,
    created_at: str,
    execution_code_commit: str,
) -> HAIOfficialDistributionMetadataV1:
    """Sanitize official Kaggle API responses into a frozen public receipt."""

    expected_ref = f"{owner}/{slug}"
    if dataset_view.get("ownerRef") != owner or dataset_view.get("ref") != expected_ref:
        raise HAIDistributionError("Kaggle dataset identity does not match the freeze")
    if int(dataset_view.get("currentVersionNumber", 0)) != dataset_version_identifier:
        raise HAIDistributionError("requested Kaggle dataset version is not current")
    versions = dataset_view.get("versions")
    if not isinstance(versions, list):
        raise HAIDistributionError("Kaggle version inventory is missing")
    matches = [
        item
        for item in versions
        if isinstance(item, Mapping)
        and int(item.get("versionNumber", 0)) == dataset_version_identifier
    ]
    if len(matches) != 1:
        raise HAIDistributionError("Kaggle version identifier is ambiguous")
    version_timestamp = str(matches[0].get("creationDate", ""))
    raw_files = file_list.get("datasetFiles")
    if not isinstance(raw_files, list) or file_list.get("nextPageToken") not in {"", None}:
        raise HAIDistributionError("complete Kaggle file inventory was not returned")
    inventory = tuple(
        sorted(
            (
                KaggleDistributionFileV1(
                    name=str(item["name"]),
                    advertised_size_bytes=int(item["totalBytes"]),
                    creation_date=str(item["creationDate"]),
                    file_type=str(item.get("fileType") or "unknown"),
                )
                for item in raw_files
                if isinstance(item, Mapping)
            ),
            key=lambda item: item.name,
        )
    )
    inventory_by_name = {item.name: item for item in inventory}
    if len(inventory_by_name) != len(inventory):
        raise HAIDistributionError("Kaggle inventory contains duplicate names")
    for expected in expected_files:
        name = str(expected["relative_path"])
        if name not in inventory_by_name:
            raise HAIDistributionError("approved HAI 23.05 file is absent from Kaggle")
        if inventory_by_name[name].advertised_size_bytes != int(expected["byte_size"]):
            raise HAIDistributionError("Kaggle advertised size differs from Git-LFS")
    return HAIOfficialDistributionMetadataV1(
        task_id="TASK-039AR",
        owner=owner,
        slug=slug,
        dataset_ref=expected_ref,
        dataset_version_identifier=dataset_version_identifier,
        version_timestamp=version_timestamp,
        license_name=str(dataset_view.get("licenseName", "")),
        complete_file_inventory=inventory,
        complete_file_inventory_count=len(inventory),
        official_git_repository=official_git_repository,
        official_git_snapshot_commit=official_git_snapshot_commit,
        introduction_commit=introduction_commit,
        task039a_expected_config_hash=task039a_expected_config_hash,
        kaggle_client_name=KAGGLE_CLIENT_NAME,
        kaggle_client_version=KAGGLE_CLIENT_VERSION,
        kaggle_api_version=KAGGLE_API_VERSION,
        metadata_endpoint=metadata_endpoint,
        file_inventory_endpoint=file_inventory_endpoint,
        selective_download_endpoint_template=selective_download_endpoint_template,
        complete_inventory_frozen=True,
        credentials_included=False,
        signed_urls_included=False,
        created_at=created_at,
        execution_code_commit=execution_code_commit,
    )
