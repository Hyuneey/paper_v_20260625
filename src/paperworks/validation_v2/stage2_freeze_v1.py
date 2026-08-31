"""Fail-closed Stage-2 preregistration and Commit-A custody.

The manifest binds only explicitly named public source, test, configuration,
and preregistration files.  It never discovers scientific data and it grants
no authority to execute test1, labels, held-out data, or a provider.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha1, sha256
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


STAGE2_FREEZE_VERSION = "VALIDATION_V2_STAGE2_COMMIT_A_V1"
_HEX = frozenset("0123456789abcdef")


class Stage2FreezeError(ValueError):
    pass


def _fail(code: str) -> None:
    raise Stage2FreezeError(code)


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _hash_document(value: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _sha(value: object, code: str) -> str:
    if type(value) is not str or len(value) != 64 or set(value) - _HEX:
        _fail(code)
    return value


def _relative_path(value: object) -> str:
    if type(value) is not str or not value or "\\" in value:
        _fail("STAGE2_PATH_INVALID")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        _fail("STAGE2_PATH_INVALID")
    return path.as_posix()


def validate_stage2_preregistration_document_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict:
        _fail("STAGE2_PREREGISTRATION_NOT_OBJECT")
    required = {
        "schema", "schema_version", "experiment_id", "status",
        "preregistration_hash",
    }
    if required - set(document):
        _fail("STAGE2_PREREGISTRATION_FIELDS_MISSING")
    if document["schema"] != "paperworks.validation_v2.stage2_preregistration_v1":
        _fail("STAGE2_PREREGISTRATION_SCHEMA_INVALID")
    if document["schema_version"] != "1.0.0":
        _fail("STAGE2_PREREGISTRATION_VERSION_INVALID")
    if type(document["experiment_id"]) is not str or not document["experiment_id"]:
        _fail("STAGE2_EXPERIMENT_ID_INVALID")
    if type(document["status"]) is not str or not (
        document["status"].startswith("FROZEN_BEFORE_")
        or document["status"] == "FROZEN_PROVIDER_GATED_DG03"
    ):
        _fail("STAGE2_PREREGISTRATION_STATUS_INVALID")
    expected = _sha(document["preregistration_hash"], "STAGE2_PREREGISTRATION_HASH_INVALID")
    body = dict(document)
    body.pop("preregistration_hash")
    if _hash_document(body) != expected:
        _fail("STAGE2_PREREGISTRATION_HASH_MISMATCH")
    serialized = json.dumps(document, sort_keys=True).lower()
    for forbidden in ('"test2_authorized": true', '"heldout_authorized": true'):
        if forbidden in serialized:
            _fail("STAGE2_FORBIDDEN_INPUT_AUTHORIZED")
    return expected


@dataclass(frozen=True)
class Stage2TrackedFileV1:
    path: str
    role: str
    experiment_ids: tuple[str, ...]
    byte_count: int
    sha256: str
    git_blob_oid: str
    git_mode: str = "100644"

    def __post_init__(self) -> None:
        _relative_path(self.path)
        if type(self.role) is not str or not self.role:
            _fail("STAGE2_FILE_ROLE_INVALID")
        if (
            type(self.experiment_ids) is not tuple
            or not self.experiment_ids
            or self.experiment_ids != tuple(sorted(set(self.experiment_ids)))
        ):
            _fail("STAGE2_EXPERIMENT_IDS_INVALID")
        if type(self.byte_count) is not int or self.byte_count <= 0:
            _fail("STAGE2_BYTE_COUNT_INVALID")
        _sha(self.sha256, "STAGE2_FILE_SHA256_INVALID")
        if type(self.git_blob_oid) is not str or len(self.git_blob_oid) != 40 or set(self.git_blob_oid) - _HEX:
            _fail("STAGE2_GIT_BLOB_OID_INVALID")
        if self.git_mode != "100644":
            _fail("STAGE2_GIT_MODE_INVALID")

    def to_dict(self) -> dict[str, Any]:
        return {
            "byte_count": self.byte_count,
            "experiment_ids": list(self.experiment_ids),
            "git_blob_oid": self.git_blob_oid,
            "git_mode": self.git_mode,
            "path": self.path,
            "role": self.role,
            "sha256": self.sha256,
        }


def bind_stage2_file_v1(
    repository_root: Path,
    *,
    path: str,
    role: str,
    experiment_ids: tuple[str, ...],
) -> Stage2TrackedFileV1:
    relative = _relative_path(path)
    root = repository_root.resolve(strict=True)
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    if candidate.is_symlink() or not candidate.is_file():
        _fail("STAGE2_FILE_MISSING_OR_SYMLINK")
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError:
        _fail("STAGE2_FILE_ESCAPES_REPOSITORY")
    raw = resolved.read_bytes()
    if not raw:
        _fail("STAGE2_FILE_EMPTY")
    blob = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    return Stage2TrackedFileV1(
        path=relative,
        role=role,
        experiment_ids=experiment_ids,
        byte_count=len(raw),
        sha256=sha256(raw).hexdigest(),
        git_blob_oid=sha1(blob).hexdigest(),
    )


@dataclass(frozen=True)
class Stage2CommitAManifestV1:
    source_base_commit: str
    authority_mode: str
    tracked_files: tuple[Stage2TrackedFileV1, ...]
    preregistration_hashes: tuple[tuple[str, str], ...]
    pilot_v1_preservation_manifest_sha256: str
    validation_protocol_hash: str
    metric_contract_hash: str
    authority_contract_sha256: str
    schema_registry_hash: str
    manifest_hash: str = ""

    def __post_init__(self) -> None:
        if type(self.source_base_commit) is not str or len(self.source_base_commit) != 40 or set(self.source_base_commit) - _HEX:
            _fail("STAGE2_SOURCE_COMMIT_INVALID")
        if self.authority_mode != "FORMAL_V4_SCIENTIFIC_AUTHORITY_WITH_NARROWED_CANONICAL_CLAIMS":
            _fail("STAGE2_AUTHORITY_MODE_INVALID")
        if type(self.tracked_files) is not tuple or not self.tracked_files:
            _fail("STAGE2_TRACKED_FILES_INVALID")
        paths = tuple(item.path for item in self.tracked_files)
        if paths != tuple(sorted(set(paths))):
            _fail("STAGE2_TRACKED_FILE_ORDER_OR_DUPLICATE")
        if (
            type(self.preregistration_hashes) is not tuple
            or not self.preregistration_hashes
            or self.preregistration_hashes != tuple(sorted(set(self.preregistration_hashes)))
        ):
            _fail("STAGE2_PREREGISTRATION_BINDINGS_INVALID")
        for experiment_id, digest in self.preregistration_hashes:
            if type(experiment_id) is not str or not experiment_id:
                _fail("STAGE2_PREREGISTRATION_ID_INVALID")
            _sha(digest, "STAGE2_PREREGISTRATION_DIGEST_INVALID")
        for value, code in (
            (self.pilot_v1_preservation_manifest_sha256, "STAGE2_PILOT_MANIFEST_HASH_INVALID"),
            (self.validation_protocol_hash, "STAGE2_PROTOCOL_HASH_INVALID"),
            (self.metric_contract_hash, "STAGE2_METRIC_HASH_INVALID"),
            (self.authority_contract_sha256, "STAGE2_AUTHORITY_CONTRACT_HASH_INVALID"),
            (self.schema_registry_hash, "STAGE2_SCHEMA_REGISTRY_HASH_INVALID"),
        ):
            _sha(value, code)
        expected = _hash_document(self.payload())
        if self.manifest_hash and self.manifest_hash != expected:
            _fail("STAGE2_MANIFEST_HASH_MISMATCH")

    def payload(self) -> dict[str, Any]:
        return {
            "authority_mode": self.authority_mode,
            "authority_contract_sha256": self.authority_contract_sha256,
            "external_provider_calls_authorized": False,
            "experiments": [
                {
                    "execution_gate": (
                        "BLOCKED_DG03" if experiment_id == "EXP-03"
                        else "BLOCKED_UNTIL_COMMIT_A_RECEIPT_AND_DATA_AUTHORITY"
                    ),
                    "experiment_id": experiment_id,
                    "heldout_authorized": False,
                    "labels_authorized": False,
                    "output_namespace": f"VALIDATION_V2/{experiment_id}",
                    "preregistration_hash": digest,
                    "test1_authorized": False,
                    "test2_authorized": False,
                }
                for experiment_id, digest in self.preregistration_hashes
            ],
            "file_manifest_hash": _hash_document({
                "tracked_files": [item.to_dict() for item in self.tracked_files]
            }),
            "heldout_access_authorized": False,
            "manifest_version": STAGE2_FREEZE_VERSION,
            "metric_contract_hash": self.metric_contract_hash,
            "normal_input_authority_status": "NOT_BOUND_NO_DATA_ACCESS_AUTHORITY",
            "phase": "PRE_SCIENCE_COMMIT_A",
            "pilot_v1_preservation_manifest_sha256": self.pilot_v1_preservation_manifest_sha256,
            "post_result_change_allowed": False,
            "program_id": "VALIDATION-V2-AUTONOMOUS-PROGRAM-V1",
            "preregistration_hashes": [
                {"experiment_id": experiment_id, "preregistration_hash": digest}
                for experiment_id, digest in self.preregistration_hashes
            ],
            "scientific_execution_authorized": False,
            "schema_registry_hash": self.schema_registry_hash,
            "source_base_commit": self.source_base_commit,
            "study_id": "VALIDATION_V2_DEVELOPMENT_V1",
            "test1_feature_access_authorized": False,
            "test1_label_access_authorized": False,
            "test2_access_authorized": False,
            "tracked_file_count": len(self.tracked_files),
            "tracked_files": [item.to_dict() for item in self.tracked_files],
            "validation_protocol_hash": self.validation_protocol_hash,
            "expected_test1_feature_authority_status": "NOT_BOUND_NO_TEST1_ACCESS_AUTHORITY",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "manifest_hash": self.manifest_hash}


def build_stage2_commit_a_manifest_v1(
    repository_root: Path,
    *,
    source_base_commit: str,
    file_bindings: Sequence[tuple[str, str, tuple[str, ...]]],
) -> Stage2CommitAManifestV1:
    if type(file_bindings) not in (tuple, list) or not file_bindings:
        _fail("STAGE2_FILE_BINDINGS_INVALID")
    records = tuple(sorted((
        bind_stage2_file_v1(
            repository_root,
            path=path,
            role=role,
            experiment_ids=experiment_ids,
        )
        for path, role, experiment_ids in file_bindings
    ), key=lambda item: item.path))
    registrations: list[tuple[str, str]] = []
    for record in records:
        if record.role != "PREREGISTRATION":
            continue
        document = json.loads((repository_root / record.path).read_text(encoding="utf-8"))
        digest = validate_stage2_preregistration_document_v1(document)
        registrations.append((document["experiment_id"], digest))
    by_path = {record.path: record for record in records}
    required_paths = {
        "pilot": "research_control_center/validation_v2/PILOT_V1_PRESERVATION_MANIFEST.json",
        "protocol": "research_control_center/validation_v2/reports/V2_PROTOCOL_001_EVIDENCE.json",
        "metric": "research_control_center/validation_v2/reports/GAP_FIX_METRIC_001_EVIDENCE.json",
        "authority": "src/paperworks/validation_v2/formal_v4_authority_v1.py",
    }
    if set(required_paths.values()) - set(by_path):
        _fail("STAGE2_REQUIRED_AUTHORITY_FILE_MISSING")
    protocol_document = json.loads((repository_root / required_paths["protocol"]).read_text(encoding="utf-8"))
    metric_document = json.loads((repository_root / required_paths["metric"]).read_text(encoding="utf-8"))
    protocol_hash = protocol_document.get("implementation", {}).get("protocol_hash")
    metric_hash = metric_document.get("implementation", {}).get("metric_contract_hash")
    _sha(protocol_hash, "STAGE2_PROTOCOL_EVIDENCE_HASH_INVALID")
    _sha(metric_hash, "STAGE2_METRIC_EVIDENCE_HASH_INVALID")
    if metric_document.get("implementation", {}).get("protocol_hash") != protocol_hash:
        _fail("STAGE2_PROTOCOL_METRIC_EVIDENCE_MISMATCH")
    schema_records = [item.to_dict() for item in records if item.role == "SCHEMA"]
    if not schema_records:
        _fail("STAGE2_SCHEMA_RECORDS_MISSING")
    provisional = Stage2CommitAManifestV1(
        source_base_commit=source_base_commit,
        authority_mode="FORMAL_V4_SCIENTIFIC_AUTHORITY_WITH_NARROWED_CANONICAL_CLAIMS",
        tracked_files=records,
        preregistration_hashes=tuple(sorted(registrations)),
        pilot_v1_preservation_manifest_sha256=by_path[required_paths["pilot"]].sha256,
        validation_protocol_hash=protocol_hash,
        metric_contract_hash=metric_hash,
        authority_contract_sha256=by_path[required_paths["authority"]].sha256,
        schema_registry_hash=_hash_document({"schema_records": schema_records}),
    )
    return replace(provisional, manifest_hash=_hash_document(provisional.payload()))


def persist_stage2_commit_a_manifest_v1(manifest: Stage2CommitAManifestV1, output_path: Path) -> None:
    if type(manifest) is not Stage2CommitAManifestV1:
        _fail("STAGE2_MANIFEST_TYPE_INVALID")
    if manifest.manifest_hash != _hash_document(manifest.payload()):
        _fail("STAGE2_MANIFEST_REPLAY_MISMATCH")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest.to_dict(), indent=2, sort_keys=True, ensure_ascii=True).encode("utf-8") + b"\n"
    try:
        descriptor = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError:
        _fail("STAGE2_MANIFEST_ALREADY_EXISTS")
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            output_path.unlink(missing_ok=True)
        finally:
            raise
    if output_path.read_bytes() != payload:
        _fail("STAGE2_MANIFEST_REOPEN_MISMATCH")
