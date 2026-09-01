"""Durable multi-method evaluation custody for VALIDATION V2.

This module is a label-blind persistence boundary.  It materializes dense,
file-local, per-second Boolean predictions outside every Git tree, publishes a
path-free receipt, freezes an exact multi-method evaluation bundle, and only
then issues an opaque one-shot capability that a caller may use to invoke its
own label reader.  The module never opens labels or scientific data.

PILOT V1 is deliberately out of scope.  All objects in this module are new V2
objects and no existing custody implementation is modified or migrated.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
from threading import Lock
from typing import Any, Callable, Mapping, TypeVar


HEX = frozenset("0123456789abcdef")
_CAPABILITY_SENTINEL = object()
_T = TypeVar("_T")


class EvaluationCustodyError(RuntimeError):
    """A fail-closed V2 persistence, binding, or replay failure."""


class EvaluationCustodyStateV1(str, Enum):
    REOPENED_AND_REPLAYED = "REOPENED_AND_REPLAYED"
    BUNDLE_FROZEN = "BUNDLE_FROZEN"
    LABEL_ACCESS_AUTHORIZED = "LABEL_ACCESS_AUTHORIZED"
    LABEL_ACCESS_CONSUMED = "LABEL_ACCESS_CONSUMED"
    POST_LABEL_VERIFIED = "POST_LABEL_VERIFIED"


def _fail(code: str) -> None:
    raise EvaluationCustodyError(code)


def _is_hex(value: object, length: int) -> bool:
    return type(value) is str and len(value) == length and set(value) <= HEX


def _require_hash(value: object, name: str) -> str:
    if not _is_hex(value, 64):
        _fail(f"INVALID_{name.upper()}_HASH")
    return value


def _require_commit(value: object) -> str:
    if not _is_hex(value, 40):
        _fail("INVALID_SOURCE_COMMIT")
    return value


def _identifier(value: object, name: str) -> str:
    if type(value) is not str or not value or len(value) > 160:
        _fail(f"INVALID_{name.upper()}")
    if any(ord(character) < 33 or ord(character) > 126 for character in value):
        _fail(f"INVALID_{name.upper()}")
    if value in (".", "..") or any(marker in value for marker in ("/", "\\", ":")):
        _fail(f"PRIVATE_PATH_SHAPED_{name.upper()}_REJECTED")
    return value


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        + b"\n"
    )


def _self_hash(document: Mapping[str, Any]) -> str:
    body = dict(document)
    body.pop("self_hash", None)
    return sha256(_canonical_bytes(body)).hexdigest()


def _require_exact_keys(document: Mapping[str, Any], keys: frozenset[str], object_name: str) -> None:
    if type(document) is not dict:
        _fail(f"{object_name}_NOT_EXACT_OBJECT")
    if frozenset(document) != keys:
        _fail(f"{object_name}_FIELDS_MISMATCH")


@dataclass(frozen=True)
class DenseBooleanPredictionRecordV1:
    """One label-blind Boolean prediction at a file-local one-second row."""

    file_id: str
    file_content_sha256: str
    row_index: int
    alarm: bool

    def __post_init__(self) -> None:
        _identifier(self.file_id, "file_id")
        if self.file_id in (".", "..") or any(marker in self.file_id for marker in ("/", "\\", ":")):
            _fail("PRIVATE_PATH_SHAPED_FILE_ID_REJECTED")
        _require_hash(self.file_content_sha256, "file_content")
        if type(self.row_index) is not int or self.row_index < 0:
            _fail("INVALID_ROW_INDEX")
        if type(self.alarm) is not bool:
            _fail("INVALID_ALARM")

    def to_document(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "file_content_sha256": self.file_content_sha256,
            "row_index": self.row_index,
            "alarm": self.alarm,
        }


@dataclass(frozen=True)
class DenseBooleanPredictionArtifactV1:
    """A complete dense per-second prediction for one evaluation method."""

    artifact_id: str
    method_id: str
    config_id: str
    experiment_id: str
    dataset_id: str
    split_role: str
    authority_hash: str
    evaluation_policy_hash: str
    metric_contract_hash: str
    file_contract_hash: str
    source_commit: str
    records: tuple[DenseBooleanPredictionRecordV1, ...]

    def __post_init__(self) -> None:
        for name in ("artifact_id", "method_id", "config_id", "experiment_id", "dataset_id"):
            _identifier(getattr(self, name), name)
        if self.split_role != "DEVELOPMENT_TEST1":
            _fail("SPLIT_ROLE_NOT_DEVELOPMENT_TEST1")
        for name in ("authority", "evaluation_policy", "metric_contract", "file_contract"):
            _require_hash(getattr(self, f"{name}_hash"), name)
        _require_commit(self.source_commit)
        if type(self.records) is not tuple or not self.records:
            _fail("PREDICTION_RECORDS_MUST_BE_NONEMPTY_TUPLE")
        if any(type(record) is not DenseBooleanPredictionRecordV1 for record in self.records):
            _fail("WRONG_PREDICTION_RECORD_TYPE")
        coordinates = tuple((record.file_id, record.row_index) for record in self.records)
        if coordinates != tuple(sorted(set(coordinates))):
            _fail("PREDICTION_COORDINATES_MUST_BE_SORTED_UNIQUE")
        by_file: dict[str, list[DenseBooleanPredictionRecordV1]] = {}
        for record in self.records:
            by_file.setdefault(record.file_id, []).append(record)
        for records in by_file.values():
            if [record.row_index for record in records] != list(range(len(records))):
                _fail("PREDICTION_MUST_BE_DENSE_FILE_LOCAL")
            if len({record.file_content_sha256 for record in records}) != 1:
                _fail("INCONSISTENT_FILE_CONTENT_HASH")

    def to_document(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "schema": "paperworks.validation_v2.dense_boolean_prediction_artifact_v1",
            "schema_version": "1.0.0",
            "artifact_id": self.artifact_id,
            "method_id": self.method_id,
            "config_id": self.config_id,
            "experiment_id": self.experiment_id,
            "dataset_id": self.dataset_id,
            "split_role": self.split_role,
            "authority_hash": self.authority_hash,
            "evaluation_policy_hash": self.evaluation_policy_hash,
            "metric_contract_hash": self.metric_contract_hash,
            "file_contract_hash": self.file_contract_hash,
            "source_commit": self.source_commit,
            "sample_period_seconds": 1,
            "label_blind": True,
            "record_count": len(self.records),
            "alarm_count": sum(record.alarm for record in self.records),
            "records": [record.to_document() for record in self.records],
        }
        body["self_hash"] = _self_hash(body)
        return body


@dataclass(frozen=True)
class HashOnlyPredictionFreezeReceiptV1:
    """Public-safe receipt: identities and hashes, never paths or payloads."""

    artifact_id: str
    method_id: str
    prediction_bytes_sha256: str
    prediction_self_hash: str
    authority_hash: str
    evaluation_policy_hash: str
    metric_contract_hash: str
    file_contract_hash: str
    source_commit: str
    record_count: int
    alarm_count: int
    publication_method: str
    file_fsync: bool
    directory_fsync: str
    state: EvaluationCustodyStateV1
    self_hash: str

    def to_document(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.hash_only_prediction_freeze_receipt_v1",
            "schema_version": "1.0.0",
            "artifact_id": self.artifact_id,
            "method_id": self.method_id,
            "prediction_bytes_sha256": self.prediction_bytes_sha256,
            "prediction_self_hash": self.prediction_self_hash,
            "authority_hash": self.authority_hash,
            "evaluation_policy_hash": self.evaluation_policy_hash,
            "metric_contract_hash": self.metric_contract_hash,
            "file_contract_hash": self.file_contract_hash,
            "source_commit": self.source_commit,
            "record_count": self.record_count,
            "alarm_count": self.alarm_count,
            "publication_method": self.publication_method,
            "file_fsync": self.file_fsync,
            "directory_fsync": self.directory_fsync,
            "state": self.state.value,
            "self_hash": self.self_hash,
        }


@dataclass(frozen=True, repr=False)
class PredictionFreezeReferenceV1:
    """Private in-process locator paired with a path-free public receipt."""

    method_id: str
    prediction_relative_path: str
    receipt_relative_path: str
    receipt: HashOnlyPredictionFreezeReceiptV1

    def __post_init__(self) -> None:
        _identifier(self.method_id, "method_id")
        if type(self.receipt) is not HashOnlyPredictionFreezeReceiptV1:
            _fail("WRONG_PREDICTION_RECEIPT_TYPE")
        if self.receipt.method_id != self.method_id:
            _fail("REFERENCE_METHOD_RECEIPT_MISMATCH")

    def __repr__(self) -> str:
        return f"PredictionFreezeReferenceV1(method_id={self.method_id!r}, paths=<private>)"


@dataclass(frozen=True)
class HashOnlyEvaluationBundleFreezeReceiptV1:
    """Public-safe receipt for an exact frozen multi-method input bundle."""

    bundle_id: str
    exact_method_ids: tuple[str, ...]
    bundle_bytes_sha256: str
    bundle_self_hash: str
    evaluation_policy_hash: str
    metric_contract_hash: str
    source_commit: str
    prediction_receipt_hashes: tuple[str, ...]
    publication_method: str
    file_fsync: bool
    directory_fsync: str
    state: EvaluationCustodyStateV1
    self_hash: str

    def to_document(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.hash_only_evaluation_bundle_freeze_receipt_v1",
            "schema_version": "1.0.0",
            "bundle_id": self.bundle_id,
            "exact_method_ids": list(self.exact_method_ids),
            "bundle_bytes_sha256": self.bundle_bytes_sha256,
            "bundle_self_hash": self.bundle_self_hash,
            "evaluation_policy_hash": self.evaluation_policy_hash,
            "metric_contract_hash": self.metric_contract_hash,
            "source_commit": self.source_commit,
            "prediction_receipt_hashes": list(self.prediction_receipt_hashes),
            "publication_method": self.publication_method,
            "file_fsync": self.file_fsync,
            "directory_fsync": self.directory_fsync,
            "state": self.state.value,
            "self_hash": self.self_hash,
        }


class EvaluationLabelAccessCapabilityV1:
    """Opaque one-shot capability issued only after full durable replay."""

    __slots__ = ("_token",)

    def __new__(cls, sentinel: object, token: str) -> "EvaluationLabelAccessCapabilityV1":
        if sentinel is not _CAPABILITY_SENTINEL:
            _fail("FORGED_LABEL_CAPABILITY_REJECTED")
        value = super().__new__(cls)
        value._token = token
        return value

    def __repr__(self) -> str:
        return "EvaluationLabelAccessCapabilityV1(<opaque>)"


@dataclass
class _CapabilityState:
    capability: EvaluationLabelAccessCapabilityV1
    bound_files: tuple[tuple[Path, str, str], ...]
    evaluation_policy_hash: str
    metric_contract_hash: str
    source_commit: str
    exact_method_ids: tuple[str, ...]
    state: EvaluationCustodyStateV1


@dataclass(frozen=True)
class _ReplayedPredictionReference:
    prediction_path: Path
    receipt_path: Path
    receipt: HashOnlyPredictionFreezeReceiptV1
    artifact: DenseBooleanPredictionArtifactV1
    prediction_bytes_sha256: str
    receipt_bytes_sha256: str


@dataclass(frozen=True)
class _ReplayedEvaluationBundle:
    bundle_path: Path
    receipt_path: Path
    bundle_bytes_sha256: str
    receipt_bytes_sha256: str


_CAPABILITIES: dict[str, _CapabilityState] = {}
_CAPABILITY_LOCK = Lock()
_PUBLICATION_LOCK = Lock()
_PUBLISHED_PREDICTIONS: dict[tuple[str, str], tuple[Path, Path, HashOnlyPredictionFreezeReceiptV1]] = {}
_PUBLISHED_BUNDLES: dict[tuple[str, str], tuple[Path, Path, HashOnlyEvaluationBundleFreezeReceiptV1]] = {}


def _validated_root(root: Path) -> Path:
    if not isinstance(root, Path):
        _fail("ARTIFACT_ROOT_MUST_BE_PATH")
    if not root.is_absolute():
        _fail("ARTIFACT_ROOT_MUST_BE_ABSOLUTE")
    if (
        not root.exists()
        or not root.is_dir()
        or root.is_symlink()
        or getattr(root, "is_junction", lambda: False)()
    ):
        _fail("INVALID_ARTIFACT_ROOT")
    resolved = root.resolve(strict=True)
    if any((candidate / ".git").exists() for candidate in (resolved, *resolved.parents)):
        _fail("GIT_INTERNAL_CUSTODY_ROOT_REJECTED")
    return resolved


def _resolve_relative(root: Path, relative: str, *, create_parents: bool) -> Path:
    if type(relative) is not str or not relative or "\\" in relative or ":" in relative:
        _fail("INVALID_RELATIVE_PATH")
    raw_parts = relative.split("/")
    if any(part in ("", ".", "..") for part in raw_parts):
        _fail("INVALID_RELATIVE_PATH")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        _fail("INVALID_RELATIVE_PATH")
    current = root
    for part in pure.parts[:-1]:
        current = current / part
        if current.exists() and (
            current.is_symlink() or getattr(current, "is_junction", lambda: False)()
        ):
            _fail("LINKED_PARENT_PATH_REJECTED")
        if create_parents:
            current.mkdir(exist_ok=True)
        if (
            not current.exists()
            or not current.is_dir()
            or current.is_symlink()
            or getattr(current, "is_junction", lambda: False)()
        ):
            _fail("INVALID_PARENT_DIRECTORY")
        try:
            current.resolve(strict=True).relative_to(root)
        except ValueError:
            _fail("PATH_ESCAPE_REJECTED")
    target = current / pure.name
    if current.resolve(strict=True) != target.parent.resolve(strict=True):
        _fail("PATH_ESCAPE_REJECTED")
    if target.exists() and (
        target.is_symlink() or getattr(target, "is_junction", lambda: False)()
    ):
        _fail("LINKED_TARGET_PATH_REJECTED")
    return target


def _assert_regular_file(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        _fail("ARTIFACT_MISSING")
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        _fail("NONREGULAR_ARTIFACT_REJECTED")


def _directory_fsync(parent: Path) -> str:
    if os.name == "nt":
        return "UNSUPPORTED_WINDOWS"
    try:
        descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        _fail("DIRECTORY_FSYNC_FAILED")
    return "PERFORMED"


def _publish_no_overwrite(target: Path, content: bytes) -> tuple[bytes, str]:
    temporary = target.with_name(target.name + ".tmp")
    if target.exists() or target.is_symlink():
        _fail("STALE_DESTINATION_REJECTED")
    if temporary.exists() or temporary.is_symlink():
        _fail("STALE_TEMPORARY_REJECTED")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        _assert_regular_file(temporary)
        os.link(temporary, target, follow_symlinks=False)
        temporary.unlink()
        directory_fsync = _directory_fsync(target.parent)
        _assert_regular_file(target)
        replay = target.read_bytes()
        if replay != content:
            _fail("PUBLISHED_BYTES_DIFFER")
        return replay, directory_fsync
    except EvaluationCustodyError:
        raise
    except FileExistsError:
        _fail("NO_OVERWRITE_PUBLISH_REJECTED")
    except OSError as error:
        _fail(f"ATOMIC_PUBLISH_FAILED_{type(error).__name__.upper()}")
    finally:
        if temporary.exists() and not temporary.is_symlink():
            try:
                temporary.unlink()
            except OSError:
                pass
    raise AssertionError("unreachable")


_PREDICTION_KEYS = frozenset(
    {
        "schema", "schema_version", "artifact_id", "method_id", "config_id", "experiment_id",
        "dataset_id", "split_role", "authority_hash", "evaluation_policy_hash", "metric_contract_hash",
        "file_contract_hash", "source_commit", "sample_period_seconds", "label_blind", "record_count",
        "alarm_count", "records", "self_hash",
    }
)


def validate_dense_prediction_document_v1(
    document: Mapping[str, Any], *, expected_method_id: str | None = None
) -> DenseBooleanPredictionArtifactV1:
    _require_exact_keys(document, _PREDICTION_KEYS, "PREDICTION_DOCUMENT")
    if document["schema"] != "paperworks.validation_v2.dense_boolean_prediction_artifact_v1":
        _fail("WRONG_PREDICTION_SCHEMA")
    if document["schema_version"] != "1.0.0" or document["sample_period_seconds"] != 1:
        _fail("WRONG_PREDICTION_VERSION_OR_SAMPLE_PERIOD")
    if document["label_blind"] is not True:
        _fail("PREDICTION_NOT_LABEL_BLIND")
    if document["self_hash"] != _self_hash(document):
        _fail("PREDICTION_SELF_HASH_MISMATCH")
    if type(document["records"]) is not list:
        _fail("PREDICTION_RECORDS_NOT_LIST")
    records: list[DenseBooleanPredictionRecordV1] = []
    for item in document["records"]:
        _require_exact_keys(item, frozenset({"file_id", "file_content_sha256", "row_index", "alarm"}), "PREDICTION_RECORD")
        records.append(DenseBooleanPredictionRecordV1(**item))
    artifact = DenseBooleanPredictionArtifactV1(
        artifact_id=document["artifact_id"], method_id=document["method_id"], config_id=document["config_id"],
        experiment_id=document["experiment_id"], dataset_id=document["dataset_id"], split_role=document["split_role"],
        authority_hash=document["authority_hash"], evaluation_policy_hash=document["evaluation_policy_hash"],
        metric_contract_hash=document["metric_contract_hash"], file_contract_hash=document["file_contract_hash"],
        source_commit=document["source_commit"], records=tuple(records),
    )
    if expected_method_id is not None and artifact.method_id != expected_method_id:
        _fail("WRONG_PREDICTION_METHOD")
    if document["record_count"] != len(records) or document["alarm_count"] != sum(record.alarm for record in records):
        _fail("PREDICTION_COUNT_MISMATCH")
    if artifact.to_document() != document:
        _fail("PREDICTION_REPLAY_MISMATCH")
    return artifact


_PREDICTION_RECEIPT_KEYS = frozenset(
    {
        "schema", "schema_version", "artifact_id", "method_id", "prediction_bytes_sha256",
        "prediction_self_hash", "authority_hash", "evaluation_policy_hash", "metric_contract_hash",
        "file_contract_hash", "source_commit", "record_count", "alarm_count", "publication_method",
        "file_fsync", "directory_fsync", "state", "self_hash",
    }
)


def _validate_prediction_receipt_document(document: Mapping[str, Any]) -> HashOnlyPredictionFreezeReceiptV1:
    _require_exact_keys(document, _PREDICTION_RECEIPT_KEYS, "PREDICTION_RECEIPT")
    if document["schema"] != "paperworks.validation_v2.hash_only_prediction_freeze_receipt_v1":
        _fail("WRONG_PREDICTION_RECEIPT_SCHEMA")
    if document["schema_version"] != "1.0.0" or document["self_hash"] != _self_hash(document):
        _fail("PREDICTION_RECEIPT_INTEGRITY_MISMATCH")
    _identifier(document["artifact_id"], "artifact_id")
    _identifier(document["method_id"], "method_id")
    for name in (
        "prediction_bytes_sha256", "prediction_self_hash", "authority_hash", "evaluation_policy_hash",
        "metric_contract_hash", "file_contract_hash",
    ):
        _require_hash(document[name], name)
    _require_commit(document["source_commit"])
    if type(document["record_count"]) is not int or document["record_count"] <= 0:
        _fail("INVALID_RECEIPT_RECORD_COUNT")
    if type(document["alarm_count"]) is not int or not 0 <= document["alarm_count"] <= document["record_count"]:
        _fail("INVALID_RECEIPT_ALARM_COUNT")
    try:
        state = EvaluationCustodyStateV1(document["state"])
    except (TypeError, ValueError):
        _fail("INVALID_PREDICTION_RECEIPT_STATE")
    if (
        document["publication_method"] != "HARD_LINK_NO_OVERWRITE"
        or document["file_fsync"] is not True
        or document["directory_fsync"] not in ("PERFORMED", "UNSUPPORTED_WINDOWS")
        or state is not EvaluationCustodyStateV1.REOPENED_AND_REPLAYED
    ):
        _fail("PREDICTION_RECEIPT_CUSTODY_STATE_INVALID")
    receipt = HashOnlyPredictionFreezeReceiptV1(
        artifact_id=document["artifact_id"], method_id=document["method_id"],
        prediction_bytes_sha256=document["prediction_bytes_sha256"], prediction_self_hash=document["prediction_self_hash"],
        authority_hash=document["authority_hash"], evaluation_policy_hash=document["evaluation_policy_hash"],
        metric_contract_hash=document["metric_contract_hash"], file_contract_hash=document["file_contract_hash"],
        source_commit=document["source_commit"], record_count=document["record_count"], alarm_count=document["alarm_count"],
        publication_method=document["publication_method"], file_fsync=document["file_fsync"],
        directory_fsync=document["directory_fsync"], state=state, self_hash=document["self_hash"],
    )
    if receipt.to_document() != document:
        _fail("PREDICTION_RECEIPT_REPLAY_MISMATCH")
    return receipt


def persist_dense_prediction_before_label_v1(
    artifact: DenseBooleanPredictionArtifactV1,
    *,
    artifact_root: Path,
    prediction_relative_path: str,
    receipt_relative_path: str,
) -> HashOnlyPredictionFreezeReceiptV1:
    """No-overwrite persist, fsync, close, publish, reopen, and hash replay."""

    if type(artifact) is not DenseBooleanPredictionArtifactV1:
        _fail("WRONG_PREDICTION_ARTIFACT_TYPE")
    root = _validated_root(artifact_root)
    prediction_path = _resolve_relative(root, prediction_relative_path, create_parents=True)
    receipt_path = _resolve_relative(root, receipt_relative_path, create_parents=True)
    if prediction_path == receipt_path:
        _fail("PREDICTION_RECEIPT_PATH_COLLISION")
    document = artifact.to_document()
    validate_dense_prediction_document_v1(document, expected_method_id=artifact.method_id)
    prediction_bytes, directory_fsync = _publish_no_overwrite(prediction_path, _canonical_bytes(document))
    replay_document = json.loads(prediction_bytes.decode("utf-8"))
    validate_dense_prediction_document_v1(replay_document, expected_method_id=artifact.method_id)
    receipt_body: dict[str, Any] = {
        "schema": "paperworks.validation_v2.hash_only_prediction_freeze_receipt_v1",
        "schema_version": "1.0.0",
        "artifact_id": artifact.artifact_id,
        "method_id": artifact.method_id,
        "prediction_bytes_sha256": sha256(prediction_bytes).hexdigest(),
        "prediction_self_hash": replay_document["self_hash"],
        "authority_hash": artifact.authority_hash,
        "evaluation_policy_hash": artifact.evaluation_policy_hash,
        "metric_contract_hash": artifact.metric_contract_hash,
        "file_contract_hash": artifact.file_contract_hash,
        "source_commit": artifact.source_commit,
        "record_count": len(artifact.records),
        "alarm_count": sum(record.alarm for record in artifact.records),
        "publication_method": "HARD_LINK_NO_OVERWRITE",
        "file_fsync": True,
        "directory_fsync": directory_fsync,
        "state": EvaluationCustodyStateV1.REOPENED_AND_REPLAYED.value,
    }
    receipt_body["self_hash"] = _self_hash(receipt_body)
    receipt_bytes, _ = _publish_no_overwrite(receipt_path, _canonical_bytes(receipt_body))
    receipt = _validate_prediction_receipt_document(json.loads(receipt_bytes.decode("utf-8")))
    if receipt.prediction_bytes_sha256 != sha256(prediction_bytes).hexdigest():
        _fail("PREDICTION_RECEIPT_BINDING_MISMATCH")
    with _PUBLICATION_LOCK:
        _PUBLISHED_PREDICTIONS[(str(root), receipt.self_hash)] = (prediction_path, receipt_path, receipt)
    return receipt


def _replay_prediction_reference(
    root: Path,
    reference: PredictionFreezeReferenceV1,
    *,
    expected_policy_hash: str,
    expected_metric_contract_hash: str,
    expected_source_commit: str,
) -> _ReplayedPredictionReference:
    prediction_path = _resolve_relative(root, reference.prediction_relative_path, create_parents=False)
    receipt_path = _resolve_relative(root, reference.receipt_relative_path, create_parents=False)
    with _PUBLICATION_LOCK:
        published = _PUBLISHED_PREDICTIONS.get((str(root), reference.receipt.self_hash))
    if published != (prediction_path, receipt_path, reference.receipt):
        _fail("STALE_OR_WRONG_PREDICTION_RECEIPT_REFERENCE_UNPUBLISHED")
    _assert_regular_file(prediction_path)
    _assert_regular_file(receipt_path)
    prediction_bytes = prediction_path.read_bytes()
    receipt_bytes = receipt_path.read_bytes()
    try:
        receipt = _validate_prediction_receipt_document(json.loads(receipt_bytes.decode("utf-8")))
        artifact = validate_dense_prediction_document_v1(
            json.loads(prediction_bytes.decode("utf-8")), expected_method_id=reference.method_id
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("PREDICTION_REFERENCE_NOT_CANONICAL_JSON")
    if receipt != reference.receipt:
        _fail("STALE_OR_WRONG_PREDICTION_RECEIPT_REFERENCE")
    if receipt.method_id != reference.method_id or artifact.method_id != reference.method_id:
        _fail("REFERENCE_METHOD_BINDING_MISMATCH")
    if sha256(prediction_bytes).hexdigest() != receipt.prediction_bytes_sha256:
        _fail("PREDICTION_BYTES_RECEIPT_MISMATCH")
    if artifact.to_document()["self_hash"] != receipt.prediction_self_hash:
        _fail("PREDICTION_SELF_HASH_RECEIPT_MISMATCH")
    if artifact.artifact_id != receipt.artifact_id:
        _fail("PREDICTION_ARTIFACT_ID_RECEIPT_MISMATCH")
    if artifact.authority_hash != receipt.authority_hash:
        _fail("PREDICTION_AUTHORITY_RECEIPT_MISMATCH")
    if artifact.file_contract_hash != receipt.file_contract_hash:
        _fail("PREDICTION_FILE_CONTRACT_RECEIPT_MISMATCH")
    if len(artifact.records) != receipt.record_count:
        _fail("PREDICTION_RECORD_COUNT_RECEIPT_MISMATCH")
    if sum(record.alarm for record in artifact.records) != receipt.alarm_count:
        _fail("PREDICTION_ALARM_COUNT_RECEIPT_MISMATCH")
    if artifact.evaluation_policy_hash != expected_policy_hash or receipt.evaluation_policy_hash != expected_policy_hash:
        _fail("WRONG_EVALUATION_POLICY_REFERENCE")
    if artifact.metric_contract_hash != expected_metric_contract_hash or receipt.metric_contract_hash != expected_metric_contract_hash:
        _fail("WRONG_METRIC_CONTRACT_REFERENCE")
    if artifact.source_commit != expected_source_commit or receipt.source_commit != expected_source_commit:
        _fail("WRONG_SOURCE_COMMIT_REFERENCE")
    return _ReplayedPredictionReference(
        prediction_path=prediction_path,
        receipt_path=receipt_path,
        receipt=receipt,
        artifact=artifact,
        prediction_bytes_sha256=receipt.prediction_bytes_sha256,
        receipt_bytes_sha256=sha256(receipt_bytes).hexdigest(),
    )


def replay_dense_prediction_before_label_v1(
    *, artifact_root: Path, reference: PredictionFreezeReferenceV1,
    expected_policy_hash: str, expected_metric_contract_hash: str,
    expected_source_commit: str,
) -> DenseBooleanPredictionArtifactV1:
    """Replay one durable dense prediction without authorizing label access."""

    root = _validated_root(artifact_root)
    replayed = _replay_prediction_reference(
        root, reference, expected_policy_hash=expected_policy_hash,
        expected_metric_contract_hash=expected_metric_contract_hash,
        expected_source_commit=expected_source_commit,
    )
    return replayed.artifact


def _validate_exact_method_set(exact_method_ids: tuple[str, ...]) -> tuple[str, ...]:
    if type(exact_method_ids) is not tuple or not exact_method_ids:
        _fail("EXACT_METHOD_SET_MUST_BE_NONEMPTY_TUPLE")
    for method_id in exact_method_ids:
        _identifier(method_id, "method_id")
    if exact_method_ids != tuple(sorted(set(exact_method_ids))):
        _fail("EXACT_METHOD_SET_MUST_BE_SORTED_UNIQUE")
    return exact_method_ids


def _validate_references(
    references: tuple[PredictionFreezeReferenceV1, ...], exact_method_ids: tuple[str, ...]
) -> tuple[PredictionFreezeReferenceV1, ...]:
    if type(references) is not tuple or any(type(item) is not PredictionFreezeReferenceV1 for item in references):
        _fail("PREDICTION_REFERENCES_MUST_BE_EXACT_TUPLE")
    method_ids = tuple(item.method_id for item in references)
    if method_ids != tuple(sorted(method_ids)):
        _fail("PREDICTION_REFERENCES_MUST_BE_METHOD_SORTED")
    if len(set(method_ids)) != len(method_ids):
        _fail("DUPLICATE_METHOD_REFERENCE_REJECTED")
    if method_ids != exact_method_ids:
        _fail("MISSING_OR_EXTRA_METHOD_REFERENCE_REJECTED")
    return references


def _bundle_document(
    *, bundle_id: str, exact_method_ids: tuple[str, ...], receipts: tuple[HashOnlyPredictionFreezeReceiptV1, ...],
    evaluation_policy_hash: str, metric_contract_hash: str, source_commit: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": "paperworks.validation_v2.multi_method_evaluation_bundle_v1",
        "schema_version": "1.0.0",
        "bundle_id": bundle_id,
        "exact_method_ids": list(exact_method_ids),
        "evaluation_policy_hash": evaluation_policy_hash,
        "metric_contract_hash": metric_contract_hash,
        "source_commit": source_commit,
        "label_blind": True,
        "methods": [
            {
                "method_id": receipt.method_id,
                "prediction_receipt_hash": receipt.self_hash,
                "prediction_bytes_sha256": receipt.prediction_bytes_sha256,
                "authority_hash": receipt.authority_hash,
            }
            for receipt in receipts
        ],
    }
    body["self_hash"] = _self_hash(body)
    return body


_BUNDLE_RECEIPT_KEYS = frozenset(
    {
        "schema", "schema_version", "bundle_id", "exact_method_ids", "bundle_bytes_sha256", "bundle_self_hash",
        "evaluation_policy_hash", "metric_contract_hash", "source_commit", "prediction_receipt_hashes",
        "publication_method", "file_fsync", "directory_fsync", "state", "self_hash",
    }
)


def _validate_bundle_receipt_document(document: Mapping[str, Any]) -> HashOnlyEvaluationBundleFreezeReceiptV1:
    _require_exact_keys(document, _BUNDLE_RECEIPT_KEYS, "BUNDLE_RECEIPT")
    if document["schema"] != "paperworks.validation_v2.hash_only_evaluation_bundle_freeze_receipt_v1":
        _fail("WRONG_BUNDLE_RECEIPT_SCHEMA")
    if document["schema_version"] != "1.0.0" or document["self_hash"] != _self_hash(document):
        _fail("BUNDLE_RECEIPT_INTEGRITY_MISMATCH")
    _identifier(document["bundle_id"], "bundle_id")
    methods = tuple(document["exact_method_ids"])
    _validate_exact_method_set(methods)
    receipt_hashes = tuple(document["prediction_receipt_hashes"])
    if len(receipt_hashes) != len(methods) or any(not _is_hex(value, 64) for value in receipt_hashes):
        _fail("INVALID_BUNDLE_PREDICTION_RECEIPT_HASHES")
    for name in ("bundle_bytes_sha256", "bundle_self_hash", "evaluation_policy_hash", "metric_contract_hash"):
        _require_hash(document[name], name)
    _require_commit(document["source_commit"])
    try:
        state = EvaluationCustodyStateV1(document["state"])
    except (TypeError, ValueError):
        _fail("INVALID_BUNDLE_RECEIPT_STATE")
    if (
        document["publication_method"] != "HARD_LINK_NO_OVERWRITE"
        or document["file_fsync"] is not True
        or document["directory_fsync"] not in ("PERFORMED", "UNSUPPORTED_WINDOWS")
        or state is not EvaluationCustodyStateV1.BUNDLE_FROZEN
    ):
        _fail("BUNDLE_RECEIPT_CUSTODY_STATE_INVALID")
    receipt = HashOnlyEvaluationBundleFreezeReceiptV1(
        bundle_id=document["bundle_id"], exact_method_ids=methods, bundle_bytes_sha256=document["bundle_bytes_sha256"],
        bundle_self_hash=document["bundle_self_hash"], evaluation_policy_hash=document["evaluation_policy_hash"],
        metric_contract_hash=document["metric_contract_hash"], source_commit=document["source_commit"],
        prediction_receipt_hashes=receipt_hashes, publication_method=document["publication_method"],
        file_fsync=document["file_fsync"], directory_fsync=document["directory_fsync"], state=state,
        self_hash=document["self_hash"],
    )
    if receipt.to_document() != document:
        _fail("BUNDLE_RECEIPT_REPLAY_MISMATCH")
    return receipt


def freeze_multi_method_evaluation_bundle_v1(
    *,
    artifact_root: Path,
    bundle_id: str,
    exact_method_ids: tuple[str, ...],
    prediction_references: tuple[PredictionFreezeReferenceV1, ...],
    evaluation_policy_hash: str,
    metric_contract_hash: str,
    source_commit: str,
    bundle_relative_path: str,
    bundle_receipt_relative_path: str,
) -> HashOnlyEvaluationBundleFreezeReceiptV1:
    """Freeze an exact method set after replaying every durable prediction."""

    _identifier(bundle_id, "bundle_id")
    methods = _validate_exact_method_set(exact_method_ids)
    references = _validate_references(prediction_references, methods)
    _require_hash(evaluation_policy_hash, "evaluation_policy")
    _require_hash(metric_contract_hash, "metric_contract")
    _require_commit(source_commit)
    root = _validated_root(artifact_root)
    bundle_path = _resolve_relative(root, bundle_relative_path, create_parents=True)
    bundle_receipt_path = _resolve_relative(root, bundle_receipt_relative_path, create_parents=True)
    if bundle_path == bundle_receipt_path:
        _fail("BUNDLE_RECEIPT_PATH_COLLISION")
    replayed = tuple(
        _replay_prediction_reference(
            root, reference, expected_policy_hash=evaluation_policy_hash,
            expected_metric_contract_hash=metric_contract_hash, expected_source_commit=source_commit,
        )
        for reference in references
    )
    receipts = tuple(item.receipt for item in replayed)
    bundle_body = _bundle_document(
        bundle_id=bundle_id, exact_method_ids=methods, receipts=receipts,
        evaluation_policy_hash=evaluation_policy_hash, metric_contract_hash=metric_contract_hash,
        source_commit=source_commit,
    )
    bundle_bytes, directory_fsync = _publish_no_overwrite(bundle_path, _canonical_bytes(bundle_body))
    if json.loads(bundle_bytes.decode("utf-8")) != bundle_body:
        _fail("BUNDLE_REPLAY_MISMATCH")
    receipt_body: dict[str, Any] = {
        "schema": "paperworks.validation_v2.hash_only_evaluation_bundle_freeze_receipt_v1",
        "schema_version": "1.0.0",
        "bundle_id": bundle_id,
        "exact_method_ids": list(methods),
        "bundle_bytes_sha256": sha256(bundle_bytes).hexdigest(),
        "bundle_self_hash": bundle_body["self_hash"],
        "evaluation_policy_hash": evaluation_policy_hash,
        "metric_contract_hash": metric_contract_hash,
        "source_commit": source_commit,
        "prediction_receipt_hashes": [receipt.self_hash for receipt in receipts],
        "publication_method": "HARD_LINK_NO_OVERWRITE",
        "file_fsync": True,
        "directory_fsync": directory_fsync,
        "state": EvaluationCustodyStateV1.BUNDLE_FROZEN.value,
    }
    receipt_body["self_hash"] = _self_hash(receipt_body)
    receipt_bytes, _ = _publish_no_overwrite(bundle_receipt_path, _canonical_bytes(receipt_body))
    receipt = _validate_bundle_receipt_document(json.loads(receipt_bytes.decode("utf-8")))
    if receipt.bundle_bytes_sha256 != sha256(bundle_bytes).hexdigest():
        _fail("BUNDLE_RECEIPT_BINDING_MISMATCH")
    with _PUBLICATION_LOCK:
        _PUBLISHED_BUNDLES[(str(root), receipt.self_hash)] = (bundle_path, bundle_receipt_path, receipt)
    return receipt


def _replay_bundle(
    *, root: Path, bundle_relative_path: str, bundle_receipt_relative_path: str,
    expected_bundle_receipt: HashOnlyEvaluationBundleFreezeReceiptV1,
    expected_method_ids: tuple[str, ...], expected_policy_hash: str,
    expected_metric_contract_hash: str, expected_source_commit: str,
    prediction_receipts: tuple[HashOnlyPredictionFreezeReceiptV1, ...],
) -> _ReplayedEvaluationBundle:
    bundle_path = _resolve_relative(root, bundle_relative_path, create_parents=False)
    bundle_receipt_path = _resolve_relative(root, bundle_receipt_relative_path, create_parents=False)
    with _PUBLICATION_LOCK:
        published = _PUBLISHED_BUNDLES.get((str(root), expected_bundle_receipt.self_hash))
    if published != (bundle_path, bundle_receipt_path, expected_bundle_receipt):
        _fail("ARTIFACT_MISSING_OR_UNPUBLISHED_BUNDLE")
    _assert_regular_file(bundle_path)
    _assert_regular_file(bundle_receipt_path)
    try:
        bundle_bytes = bundle_path.read_bytes()
        receipt_bytes = bundle_receipt_path.read_bytes()
        bundle = json.loads(bundle_bytes.decode("utf-8"))
        receipt = _validate_bundle_receipt_document(json.loads(receipt_bytes.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("BUNDLE_NOT_CANONICAL_JSON")
    if receipt != expected_bundle_receipt:
        _fail("STALE_OR_WRONG_BUNDLE_RECEIPT")
    if (
        receipt.exact_method_ids != expected_method_ids
        or receipt.evaluation_policy_hash != expected_policy_hash
        or receipt.metric_contract_hash != expected_metric_contract_hash
        or receipt.source_commit != expected_source_commit
        or receipt.prediction_receipt_hashes != tuple(item.self_hash for item in prediction_receipts)
    ):
        _fail("BUNDLE_RECEIPT_AUTHORITY_BINDING_MISMATCH")
    expected_bundle = _bundle_document(
        bundle_id=receipt.bundle_id, exact_method_ids=expected_method_ids, receipts=prediction_receipts,
        evaluation_policy_hash=expected_policy_hash, metric_contract_hash=expected_metric_contract_hash,
        source_commit=expected_source_commit,
    )
    if bundle != expected_bundle:
        _fail("BUNDLE_CONTENT_REPLAY_MISMATCH")
    if receipt.bundle_self_hash != expected_bundle["self_hash"]:
        _fail("BUNDLE_SELF_HASH_RECEIPT_MISMATCH")
    if sha256(bundle_bytes).hexdigest() != receipt.bundle_bytes_sha256:
        _fail("BUNDLE_BYTES_RECEIPT_MISMATCH")
    return _ReplayedEvaluationBundle(
        bundle_path=bundle_path,
        receipt_path=bundle_receipt_path,
        bundle_bytes_sha256=receipt.bundle_bytes_sha256,
        receipt_bytes_sha256=sha256(receipt_bytes).hexdigest(),
    )


def authorize_evaluation_label_access_v1(
    *,
    artifact_root: Path,
    exact_method_ids: tuple[str, ...],
    prediction_references: tuple[PredictionFreezeReferenceV1, ...],
    evaluation_policy_hash: str,
    metric_contract_hash: str,
    source_commit: str,
    bundle_relative_path: str,
    bundle_receipt_relative_path: str,
    expected_bundle_receipt: HashOnlyEvaluationBundleFreezeReceiptV1,
) -> EvaluationLabelAccessCapabilityV1:
    """Replay all files and issue an opaque, durable, one-shot capability."""

    methods = _validate_exact_method_set(exact_method_ids)
    references = _validate_references(prediction_references, methods)
    _require_hash(evaluation_policy_hash, "evaluation_policy")
    _require_hash(metric_contract_hash, "metric_contract")
    _require_commit(source_commit)
    if type(expected_bundle_receipt) is not HashOnlyEvaluationBundleFreezeReceiptV1:
        _fail("WRONG_BUNDLE_RECEIPT_TYPE")
    root = _validated_root(artifact_root)
    replayed = tuple(
        _replay_prediction_reference(
            root, reference, expected_policy_hash=evaluation_policy_hash,
            expected_metric_contract_hash=metric_contract_hash, expected_source_commit=source_commit,
        )
        for reference in references
    )
    replayed_bundle = _replay_bundle(
        root=root, bundle_relative_path=bundle_relative_path,
        bundle_receipt_relative_path=bundle_receipt_relative_path,
        expected_bundle_receipt=expected_bundle_receipt, expected_method_ids=methods,
        expected_policy_hash=evaluation_policy_hash, expected_metric_contract_hash=metric_contract_hash,
        expected_source_commit=source_commit,
        prediction_receipts=tuple(item.receipt for item in replayed),
    )
    lease_body: dict[str, Any] = {
        "schema": "paperworks.validation_v2.evaluation_label_access_lease_v1",
        "schema_version": "1.0.0",
        "bundle_receipt_hash": expected_bundle_receipt.self_hash,
        "bundle_bytes_sha256": expected_bundle_receipt.bundle_bytes_sha256,
        "exact_method_ids": list(methods),
        "evaluation_policy_hash": evaluation_policy_hash,
        "metric_contract_hash": metric_contract_hash,
        "source_commit": source_commit,
        "state": EvaluationCustodyStateV1.LABEL_ACCESS_AUTHORIZED.value,
    }
    lease_body["self_hash"] = _self_hash(lease_body)
    lease_path = replayed_bundle.receipt_path.with_name(
        replayed_bundle.receipt_path.name + ".label_access_authorized"
    )
    with _CAPABILITY_LOCK:
        lease_bytes, _ = _publish_no_overwrite(lease_path, _canonical_bytes(lease_body))
        bound: list[tuple[Path, str, str]] = []
        for item in replayed:
            bound.append((item.prediction_path, item.prediction_bytes_sha256, "PREDICTION"))
            bound.append((item.receipt_path, item.receipt_bytes_sha256, "PREDICTION_RECEIPT"))
        bound.extend(
            (
                (
                    replayed_bundle.bundle_path,
                    replayed_bundle.bundle_bytes_sha256,
                    "BUNDLE",
                ),
                (
                    replayed_bundle.receipt_path,
                    replayed_bundle.receipt_bytes_sha256,
                    "BUNDLE_RECEIPT",
                ),
                (lease_path, sha256(lease_bytes).hexdigest(), "LABEL_LEASE"),
            )
        )
        token = secrets.token_hex(32)
        capability = EvaluationLabelAccessCapabilityV1(_CAPABILITY_SENTINEL, token)
        _CAPABILITIES[token] = _CapabilityState(
            capability=capability, bound_files=tuple(bound), evaluation_policy_hash=evaluation_policy_hash,
            metric_contract_hash=metric_contract_hash, source_commit=source_commit,
            exact_method_ids=methods, state=EvaluationCustodyStateV1.LABEL_ACCESS_AUTHORIZED,
        )
    return capability


def _capability_state(capability: EvaluationLabelAccessCapabilityV1) -> _CapabilityState:
    if type(capability) is not EvaluationLabelAccessCapabilityV1:
        _fail("FORGED_LABEL_CAPABILITY_REJECTED")
    state = _CAPABILITIES.get(capability._token)
    if state is None or state.capability is not capability:
        _fail("UNREGISTERED_LABEL_CAPABILITY_REJECTED")
    return state


def _verify_bound_files(state: _CapabilityState) -> None:
    for path, expected_hash, kind in state.bound_files:
        _assert_regular_file(path)
        if sha256(path.read_bytes()).hexdigest() != expected_hash:
            _fail(f"{kind}_MUTATED_AFTER_FREEZE")


def consume_evaluation_label_access_v1(
    capability: EvaluationLabelAccessCapabilityV1, label_reader: Callable[[], _T]
) -> _T:
    """Consume the capability exactly once after replaying all bound bytes."""

    if not callable(label_reader):
        _fail("LABEL_READER_NOT_CALLABLE")
    with _CAPABILITY_LOCK:
        state = _capability_state(capability)
        if state.state is not EvaluationCustodyStateV1.LABEL_ACCESS_AUTHORIZED:
            _fail("LABEL_CAPABILITY_ALREADY_CONSUMED")
        _verify_bound_files(state)
        state.state = EvaluationCustodyStateV1.LABEL_ACCESS_CONSUMED
    try:
        return label_reader()
    finally:
        _verify_bound_files(state)


def verify_evaluation_inputs_unchanged_v1(capability: EvaluationLabelAccessCapabilityV1) -> tuple[str, ...]:
    """Post-label identity verification for predictions, receipts, bundle, and lease."""

    with _CAPABILITY_LOCK:
        state = _capability_state(capability)
        if state.state is not EvaluationCustodyStateV1.LABEL_ACCESS_CONSUMED:
            _fail("POST_LABEL_VERIFY_OUT_OF_ORDER")
        _verify_bound_files(state)
        state.state = EvaluationCustodyStateV1.POST_LABEL_VERIFIED
        return tuple(expected_hash for _, expected_hash, _ in state.bound_files)


__all__ = [
    "DenseBooleanPredictionRecordV1", "DenseBooleanPredictionArtifactV1",
    "HashOnlyPredictionFreezeReceiptV1", "PredictionFreezeReferenceV1",
    "HashOnlyEvaluationBundleFreezeReceiptV1", "EvaluationLabelAccessCapabilityV1",
    "EvaluationCustodyStateV1", "EvaluationCustodyError",
    "persist_dense_prediction_before_label_v1", "validate_dense_prediction_document_v1",
    "replay_dense_prediction_before_label_v1",
    "freeze_multi_method_evaluation_bundle_v1", "authorize_evaluation_label_access_v1",
    "consume_evaluation_label_access_v1", "verify_evaluation_inputs_unchanged_v1",
]
