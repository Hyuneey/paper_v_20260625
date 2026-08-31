"""Durable, label-blind D1 prediction custody for VALIDATION V2.

The module is intentionally independent from the frozen PILOT V1 execution
entrypoints.  It persists a complete prediction through a no-overwrite publish,
reopens and replays it, then issues an opaque one-shot capability for label
access.  It never opens a label or scientific dataset itself.
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

from .schema_registry_v1 import validate_validation_v2_document_v1


PREDICTION_SCHEMA = "d1_prediction_artifact_v2.schema.json"
RECEIPT_SCHEMA = "durable_prediction_freeze_receipt_v1.schema.json"
LABEL_LEASE_SCHEMA = "label_access_authorization_lease_v1.schema.json"
HEX64 = frozenset("0123456789abcdef")
_FACTORY_SENTINEL = object()
_T = TypeVar("_T")


class PredictionCustodyError(RuntimeError):
    """Fail-closed custody or replay error."""


class PredictionFreezeStateV1(str, Enum):
    BUILT = "BUILT"
    TEMP_SYNCED = "TEMP_SYNCED"
    ATOMICALLY_PUBLISHED = "ATOMICALLY_PUBLISHED"
    REOPENED_AND_REPLAYED = "REOPENED_AND_REPLAYED"
    LABEL_ACCESS_AUTHORIZED = "LABEL_ACCESS_AUTHORIZED"
    LABEL_ACCESS_CONSUMED = "LABEL_ACCESS_CONSUMED"
    POST_METRIC_VERIFIED = "POST_METRIC_VERIFIED"


def _fail(code: str) -> None:
    raise PredictionCustodyError(code)


def _is_hex64(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= HEX64


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8") + b"\n"


def _self_hash(document: Mapping[str, Any]) -> str:
    body = dict(document)
    body.pop("self_hash", None)
    return sha256(_canonical_bytes(body)).hexdigest()


def _identifier(value: object, name: str) -> str:
    if type(value) is not str or not value or len(value) > 160:
        _fail(f"INVALID_{name.upper()}")
    if any(ord(ch) < 33 or ord(ch) > 126 for ch in value):
        _fail(f"INVALID_{name.upper()}")
    return value


@dataclass(frozen=True)
class D1PredictionRecordV2:
    file_id: str
    file_content_sha256: str
    row_index: int
    alarm: bool
    contributing_rule_ids: tuple[str, ...] = ()
    trace_hashes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _identifier(self.file_id, "file_id")
        if any(marker in self.file_id for marker in ("/", "\\", ":")) or self.file_id in (".", ".."):
            _fail("PRIVATE_PATH_SHAPED_FILE_ID_REJECTED")
        if not _is_hex64(self.file_content_sha256):
            _fail("INVALID_FILE_CONTENT_HASH")
        if type(self.row_index) is not int or self.row_index < 0:
            _fail("INVALID_ROW_INDEX")
        if type(self.alarm) is not bool:
            _fail("INVALID_ALARM")
        if type(self.contributing_rule_ids) is not tuple:
            _fail("MUTABLE_RULE_IDS_REJECTED")
        if type(self.trace_hashes) is not tuple:
            _fail("MUTABLE_TRACE_HASHES_REJECTED")
        for item in self.contributing_rule_ids:
            _identifier(item, "rule_id")
        if tuple(sorted(set(self.contributing_rule_ids))) != self.contributing_rule_ids:
            _fail("RULE_IDS_MUST_BE_SORTED_UNIQUE")
        if any(not _is_hex64(item) for item in self.trace_hashes):
            _fail("INVALID_TRACE_HASH")
        if tuple(sorted(set(self.trace_hashes))) != self.trace_hashes:
            _fail("TRACE_HASHES_MUST_BE_SORTED_UNIQUE")
        if self.alarm and not self.contributing_rule_ids:
            _fail("ALARM_REQUIRES_CONTRIBUTING_RULE")
        if not self.alarm and (self.contributing_rule_ids or self.trace_hashes):
            _fail("NO_ALARM_EVIDENCE_REJECTED")

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "file_content_sha256": self.file_content_sha256,
            "row_index": self.row_index,
            "alarm": self.alarm,
            "contributing_rule_ids": list(self.contributing_rule_ids),
            "trace_hashes": list(self.trace_hashes),
        }


@dataclass(frozen=True)
class D1PredictionArtifactV2:
    method_id: str
    config_id: str
    experiment_id: str
    dataset_id: str
    split_role: str
    authority_hash: str
    runtime_authorization_hash: str
    execution_context_hash: str
    source_commit: str
    portfolio_hash: str
    file_contract_hash: str
    records: tuple[D1PredictionRecordV2, ...]

    def __post_init__(self) -> None:
        for name in ("method_id", "config_id", "experiment_id", "dataset_id"):
            _identifier(getattr(self, name), name)
        if self.split_role != "DEVELOPMENT_TEST1":
            _fail("SPLIT_ROLE_NOT_DEVELOPMENT_TEST1")
        for name in ("authority_hash", "runtime_authorization_hash", "execution_context_hash", "portfolio_hash", "file_contract_hash"):
            if not _is_hex64(getattr(self, name)):
                _fail(f"INVALID_{name.upper()}")
        if type(self.source_commit) is not str or len(self.source_commit) != 40 or set(self.source_commit) - HEX64:
            _fail("INVALID_SOURCE_COMMIT")
        if type(self.records) is not tuple or not self.records:
            _fail("PREDICTION_RECORDS_MUST_BE_NONEMPTY_TUPLE")
        coordinates = tuple((record.file_id, record.row_index) for record in self.records)
        if coordinates != tuple(sorted(set(coordinates))):
            _fail("PREDICTION_COORDINATES_MUST_BE_SORTED_UNIQUE")
        file_hashes: dict[str, str] = {}
        for record in self.records:
            prior = file_hashes.setdefault(record.file_id, record.file_content_sha256)
            if prior != record.file_content_sha256:
                _fail("INCONSISTENT_FILE_CONTENT_HASH")

    def to_document(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "schema": "paperworks.validation_v2.d1_prediction_artifact_v2",
            "schema_version": "2.0.0",
            "method_id": self.method_id,
            "config_id": self.config_id,
            "experiment_id": self.experiment_id,
            "dataset_id": self.dataset_id,
            "split_role": self.split_role,
            "authority_hash": self.authority_hash,
            "runtime_authorization_hash": self.runtime_authorization_hash,
            "execution_context_hash": self.execution_context_hash,
            "source_commit": self.source_commit,
            "portfolio_hash": self.portfolio_hash,
            "file_contract_hash": self.file_contract_hash,
            "label_blind": True,
            "record_count": len(self.records),
            "alarm_count": sum(record.alarm for record in self.records),
            "records": [record.to_dict() for record in self.records],
        }
        body["self_hash"] = _self_hash(body)
        return body


@dataclass(frozen=True)
class DurablePredictionFreezeReceiptV1:
    prediction_relative_path: str
    prediction_bytes_sha256: str
    prediction_self_hash: str
    authority_hash: str
    runtime_authorization_hash: str
    execution_context_hash: str
    source_commit: str
    portfolio_hash: str
    file_contract_hash: str
    record_count: int
    publication_method: str
    file_fsync: bool
    directory_fsync: str
    state: PredictionFreezeStateV1
    self_hash: str

    def to_document(self) -> dict[str, Any]:
        return {
            "schema": "paperworks.validation_v2.durable_prediction_freeze_receipt_v1",
            "schema_version": "1.0.0",
            "prediction_relative_path": self.prediction_relative_path,
            "prediction_bytes_sha256": self.prediction_bytes_sha256,
            "prediction_self_hash": self.prediction_self_hash,
            "authority_hash": self.authority_hash,
            "runtime_authorization_hash": self.runtime_authorization_hash,
            "execution_context_hash": self.execution_context_hash,
            "source_commit": self.source_commit,
            "portfolio_hash": self.portfolio_hash,
            "file_contract_hash": self.file_contract_hash,
            "record_count": self.record_count,
            "publication_method": self.publication_method,
            "file_fsync": self.file_fsync,
            "directory_fsync": self.directory_fsync,
            "state": self.state.value,
            "self_hash": self.self_hash,
        }


class LabelAccessCapabilityV1:
    """Opaque one-shot authorization; instances are factory-custodied."""

    __slots__ = ("_token",)

    def __new__(cls, sentinel: object, token: str) -> "LabelAccessCapabilityV1":
        if sentinel is not _FACTORY_SENTINEL:
            _fail("FORGED_LABEL_CAPABILITY_REJECTED")
        value = super().__new__(cls)
        value._token = token
        return value

    def __repr__(self) -> str:
        return "LabelAccessCapabilityV1(<opaque>)"


@dataclass
class _CapabilityState:
    capability: LabelAccessCapabilityV1
    prediction_path: Path
    receipt_path: Path
    label_lease_path: Path
    prediction_bytes_sha256: str
    receipt_bytes_sha256: str
    label_lease_bytes_sha256: str
    authority_hash: str
    source_commit: str
    state: PredictionFreezeStateV1


_CAPABILITIES: dict[str, _CapabilityState] = {}
_CAPABILITY_LOCK = Lock()


def _validated_root(root: Path) -> Path:
    if not isinstance(root, Path):
        _fail("ARTIFACT_ROOT_MUST_BE_PATH")
    if not root.is_absolute():
        _fail("ARTIFACT_ROOT_MUST_BE_ABSOLUTE")
    if not root.exists() or not root.is_dir() or root.is_symlink():
        _fail("INVALID_ARTIFACT_ROOT")
    resolved = root.resolve(strict=True)
    if any((candidate / ".git").exists() for candidate in (resolved, *resolved.parents)):
        _fail("GIT_INTERNAL_CUSTODY_ROOT_REJECTED")
    return resolved


def _resolve_relative(root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative or "\\" in relative or ":" in relative:
        _fail("INVALID_RELATIVE_PATH")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        _fail("INVALID_RELATIVE_PATH")
    target = root.joinpath(*pure.parts)
    current = root
    for part in pure.parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            _fail("SYMLINK_PATH_REJECTED")
        current.mkdir(exist_ok=True)
        if not current.is_dir() or current.is_symlink():
            _fail("INVALID_PARENT_DIRECTORY")
    if target.parent.resolve(strict=True) != current.resolve(strict=True):
        _fail("PATH_ESCAPE_REJECTED")
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
        if temporary.read_bytes() != content:
            _fail("TEMPORARY_REPLAY_MISMATCH")
        os.link(temporary, target, follow_symlinks=False)
        temporary.unlink()
        directory_fsync = _directory_fsync(target.parent)
        _assert_regular_file(target)
        replay = target.read_bytes()
        if replay != content:
            _fail("PUBLISHED_BYTES_DIFFER")
        return replay, directory_fsync
    except PredictionCustodyError:
        raise
    except FileExistsError:
        _fail("NO_OVERWRITE_PUBLISH_REJECTED")
    except OSError as exc:
        _fail(f"ATOMIC_PUBLISH_FAILED_{type(exc).__name__.upper()}")
    finally:
        if temporary.exists() and not temporary.is_symlink():
            try:
                temporary.unlink()
            except OSError:
                pass
    raise AssertionError("unreachable")


def validate_prediction_document_v1(document: Mapping[str, Any], *, expected_authority_hash: str | None = None) -> D1PredictionArtifactV2:
    if type(document) is not dict:
        _fail("PREDICTION_DOCUMENT_NOT_EXACT_OBJECT")
    validate_validation_v2_document_v1(PREDICTION_SCHEMA, document)
    if document.get("self_hash") != _self_hash(document):
        _fail("PREDICTION_SELF_HASH_MISMATCH")
    if expected_authority_hash is not None and document.get("authority_hash") != expected_authority_hash:
        _fail("WRONG_PREDICTION_AUTHORITY")
    records = tuple(
        D1PredictionRecordV2(
            file_id=item["file_id"],
            file_content_sha256=item["file_content_sha256"],
            row_index=item["row_index"],
            alarm=item["alarm"],
            contributing_rule_ids=tuple(item["contributing_rule_ids"]),
            trace_hashes=tuple(item["trace_hashes"]),
        )
        for item in document["records"]
    )
    artifact = D1PredictionArtifactV2(
        method_id=document["method_id"], config_id=document["config_id"], experiment_id=document["experiment_id"],
        dataset_id=document["dataset_id"], split_role=document["split_role"], authority_hash=document["authority_hash"],
        runtime_authorization_hash=document["runtime_authorization_hash"], execution_context_hash=document["execution_context_hash"],
        source_commit=document["source_commit"], portfolio_hash=document["portfolio_hash"],
        file_contract_hash=document["file_contract_hash"], records=records,
    )
    if document["record_count"] != len(records) or document["alarm_count"] != sum(item.alarm for item in records):
        _fail("PREDICTION_COUNT_MISMATCH")
    if artifact.to_document() != document:
        _fail("PREDICTION_REPLAY_MISMATCH")
    return artifact


def _validate_receipt_document(document: Mapping[str, Any]) -> DurablePredictionFreezeReceiptV1:
    if type(document) is not dict:
        _fail("RECEIPT_DOCUMENT_NOT_EXACT_OBJECT")
    validate_validation_v2_document_v1(RECEIPT_SCHEMA, document)
    if document.get("self_hash") != _self_hash(document):
        _fail("RECEIPT_SELF_HASH_MISMATCH")
    try:
        state = PredictionFreezeStateV1(document["state"])
    except ValueError:
        _fail("INVALID_RECEIPT_STATE")
    return DurablePredictionFreezeReceiptV1(
        prediction_relative_path=document["prediction_relative_path"], prediction_bytes_sha256=document["prediction_bytes_sha256"],
        prediction_self_hash=document["prediction_self_hash"], authority_hash=document["authority_hash"],
        runtime_authorization_hash=document["runtime_authorization_hash"], execution_context_hash=document["execution_context_hash"],
        source_commit=document["source_commit"], portfolio_hash=document["portfolio_hash"],
        file_contract_hash=document["file_contract_hash"],
        record_count=document["record_count"], publication_method=document["publication_method"],
        file_fsync=document["file_fsync"], directory_fsync=document["directory_fsync"], state=state, self_hash=document["self_hash"],
    )


def validate_durable_prediction_freeze_receipt_v1(
    receipt: DurablePredictionFreezeReceiptV1,
) -> str:
    """Replay a materialized durable receipt without reading its custody path."""

    if type(receipt) is not DurablePredictionFreezeReceiptV1:
        _fail("WRONG_FREEZE_RECEIPT_TYPE")
    replay = _validate_receipt_document(receipt.to_document())
    if replay != receipt:
        _fail("FREEZE_RECEIPT_REPLAY_MISMATCH")
    return receipt.self_hash


def persist_prediction_before_label_v1(
    artifact: D1PredictionArtifactV2, *, artifact_root: Path,
    prediction_relative_path: str, receipt_relative_path: str,
) -> DurablePredictionFreezeReceiptV1:
    if type(artifact) is not D1PredictionArtifactV2:
        _fail("WRONG_PREDICTION_ARTIFACT_TYPE")
    root = _validated_root(artifact_root)
    prediction_path = _resolve_relative(root, prediction_relative_path)
    receipt_path = _resolve_relative(root, receipt_relative_path)
    if prediction_path == receipt_path:
        _fail("PREDICTION_RECEIPT_PATH_COLLISION")
    document = artifact.to_document()
    validate_prediction_document_v1(document, expected_authority_hash=artifact.authority_hash)
    prediction_bytes = _canonical_bytes(document)
    replay, directory_fsync = _publish_no_overwrite(prediction_path, prediction_bytes)
    replay_document = json.loads(replay.decode("utf-8"))
    validate_prediction_document_v1(replay_document, expected_authority_hash=artifact.authority_hash)
    receipt_body: dict[str, Any] = {
        "schema": "paperworks.validation_v2.durable_prediction_freeze_receipt_v1",
        "schema_version": "1.0.0",
        "prediction_relative_path": prediction_relative_path,
        "prediction_bytes_sha256": sha256(replay).hexdigest(),
        "prediction_self_hash": replay_document["self_hash"],
        "authority_hash": artifact.authority_hash,
        "runtime_authorization_hash": artifact.runtime_authorization_hash,
        "execution_context_hash": artifact.execution_context_hash,
        "source_commit": artifact.source_commit,
        "portfolio_hash": artifact.portfolio_hash,
        "file_contract_hash": artifact.file_contract_hash,
        "record_count": len(artifact.records),
        "publication_method": "HARD_LINK_NO_OVERWRITE",
        "file_fsync": True,
        "directory_fsync": directory_fsync,
        "state": PredictionFreezeStateV1.REOPENED_AND_REPLAYED.value,
    }
    receipt_body["self_hash"] = _self_hash(receipt_body)
    validate_validation_v2_document_v1(RECEIPT_SCHEMA, receipt_body)
    receipt_bytes = _canonical_bytes(receipt_body)
    receipt_replay, _ = _publish_no_overwrite(receipt_path, receipt_bytes)
    parsed_receipt = _validate_receipt_document(json.loads(receipt_replay.decode("utf-8")))
    if parsed_receipt.prediction_bytes_sha256 != sha256(prediction_path.read_bytes()).hexdigest():
        _fail("RECEIPT_PREDICTION_BINDING_MISMATCH")
    return parsed_receipt


def authorize_label_access_v1(
    *, artifact_root: Path, prediction_relative_path: str,
    receipt_relative_path: str, expected_authority_hash: str,
    expected_runtime_authorization_hash: str,
    expected_execution_context_hash: str,
    expected_source_commit: str,
    expected_portfolio_hash: str,
    expected_file_contract_hash: str,
) -> LabelAccessCapabilityV1:
    for name, value in (
        ("authority", expected_authority_hash),
        ("runtime_authorization", expected_runtime_authorization_hash),
        ("execution_context", expected_execution_context_hash),
        ("portfolio", expected_portfolio_hash),
        ("file_contract", expected_file_contract_hash),
    ):
        if not _is_hex64(value):
            _fail(f"INVALID_EXPECTED_{name.upper()}_HASH")
    if type(expected_source_commit) is not str or len(expected_source_commit) != 40 or set(expected_source_commit) - HEX64:
        _fail("INVALID_EXPECTED_SOURCE_COMMIT")
    root = _validated_root(artifact_root)
    prediction_path = _resolve_relative(root, prediction_relative_path)
    receipt_path = _resolve_relative(root, receipt_relative_path)
    _assert_regular_file(prediction_path)
    _assert_regular_file(receipt_path)
    prediction_bytes = prediction_path.read_bytes()
    receipt_bytes = receipt_path.read_bytes()
    try:
        prediction_document = json.loads(prediction_bytes.decode("utf-8"))
        receipt_document = json.loads(receipt_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("CUSTODY_DOCUMENT_PARSE_FAILURE")
    artifact = validate_prediction_document_v1(prediction_document, expected_authority_hash=expected_authority_hash)
    if artifact.runtime_authorization_hash != expected_runtime_authorization_hash:
        _fail("WRONG_RUNTIME_AUTHORIZATION")
    if artifact.execution_context_hash != expected_execution_context_hash:
        _fail("WRONG_EXECUTION_CONTEXT")
    if artifact.source_commit != expected_source_commit:
        _fail("WRONG_SOURCE_COMMIT")
    if artifact.portfolio_hash != expected_portfolio_hash:
        _fail("WRONG_PORTFOLIO")
    if artifact.file_contract_hash != expected_file_contract_hash:
        _fail("WRONG_FILE_CONTRACT")
    receipt = _validate_receipt_document(receipt_document)
    if receipt.state is not PredictionFreezeStateV1.REOPENED_AND_REPLAYED:
        _fail("PREDICTION_NOT_FROZEN")
    if receipt.prediction_relative_path != prediction_relative_path:
        _fail("RECEIPT_PATH_BINDING_MISMATCH")
    if receipt.prediction_bytes_sha256 != sha256(prediction_bytes).hexdigest():
        _fail("PREDICTION_BYTES_HASH_MISMATCH")
    if receipt.prediction_self_hash != prediction_document["self_hash"]:
        _fail("PREDICTION_SELF_HASH_BINDING_MISMATCH")
    if (
        receipt.authority_hash != expected_authority_hash
        or receipt.runtime_authorization_hash != artifact.runtime_authorization_hash
        or receipt.execution_context_hash != artifact.execution_context_hash
        or receipt.source_commit != artifact.source_commit
        or receipt.portfolio_hash != artifact.portfolio_hash
        or receipt.file_contract_hash != artifact.file_contract_hash
        or receipt.record_count != len(artifact.records)
    ):
        _fail("RECEIPT_AUTHORITY_OR_COUNT_MISMATCH")
    lease_body: dict[str, Any] = {
        "schema": "paperworks.validation_v2.label_access_authorization_lease_v1",
        "schema_version": "1.0.0",
        "prediction_bytes_sha256": sha256(prediction_bytes).hexdigest(),
        "freeze_receipt_bytes_sha256": sha256(receipt_bytes).hexdigest(),
        "authority_hash": artifact.authority_hash,
        "runtime_authorization_hash": artifact.runtime_authorization_hash,
        "execution_context_hash": artifact.execution_context_hash,
        "source_commit": artifact.source_commit,
        "portfolio_hash": artifact.portfolio_hash,
        "file_contract_hash": artifact.file_contract_hash,
        "state": PredictionFreezeStateV1.LABEL_ACCESS_AUTHORIZED.value,
    }
    lease_body["self_hash"] = _self_hash(lease_body)
    validate_validation_v2_document_v1(LABEL_LEASE_SCHEMA, lease_body)
    lease_bytes = _canonical_bytes(lease_body)
    label_lease_path = receipt_path.with_name(receipt_path.name + ".label_access_authorized")
    with _CAPABILITY_LOCK:
        lease_replay, _ = _publish_no_overwrite(label_lease_path, lease_bytes)
        if lease_replay != lease_bytes:
            _fail("LABEL_LEASE_REPLAY_MISMATCH")
        token = secrets.token_hex(32)
        capability = LabelAccessCapabilityV1(_FACTORY_SENTINEL, token)
        _CAPABILITIES[token] = _CapabilityState(
            capability=capability, prediction_path=prediction_path, receipt_path=receipt_path, label_lease_path=label_lease_path,
            prediction_bytes_sha256=sha256(prediction_bytes).hexdigest(), receipt_bytes_sha256=sha256(receipt_bytes).hexdigest(),
            label_lease_bytes_sha256=sha256(lease_replay).hexdigest(),
            authority_hash=expected_authority_hash, source_commit=expected_source_commit,
            state=PredictionFreezeStateV1.LABEL_ACCESS_AUTHORIZED,
        )
    return capability


def _capability_state(capability: LabelAccessCapabilityV1) -> _CapabilityState:
    if type(capability) is not LabelAccessCapabilityV1:
        _fail("FORGED_LABEL_CAPABILITY_REJECTED")
    state = _CAPABILITIES.get(capability._token)
    if state is None or state.capability is not capability:
        _fail("UNREGISTERED_LABEL_CAPABILITY_REJECTED")
    return state


def _verify_bound_bytes(state: _CapabilityState) -> None:
    _assert_regular_file(state.prediction_path)
    _assert_regular_file(state.receipt_path)
    if sha256(state.prediction_path.read_bytes()).hexdigest() != state.prediction_bytes_sha256:
        _fail("PREDICTION_MUTATED_AFTER_FREEZE")
    if sha256(state.receipt_path.read_bytes()).hexdigest() != state.receipt_bytes_sha256:
        _fail("RECEIPT_MUTATED_AFTER_FREEZE")
    _assert_regular_file(state.label_lease_path)
    if sha256(state.label_lease_path.read_bytes()).hexdigest() != state.label_lease_bytes_sha256:
        _fail("LABEL_LEASE_MUTATED_AFTER_AUTHORIZATION")


def validate_label_access_capability_v1(
    capability: LabelAccessCapabilityV1,
    *,
    expected_authority_hash: str,
    expected_source_commit: str,
) -> str:
    """Verify a live durable authorization without consuming label access."""

    if not _is_hex64(expected_authority_hash):
        _fail("INVALID_EXPECTED_AUTHORITY_HASH")
    if type(expected_source_commit) is not str or len(expected_source_commit) != 40 or set(expected_source_commit) - HEX64:
        _fail("INVALID_EXPECTED_SOURCE_COMMIT")
    with _CAPABILITY_LOCK:
        state = _capability_state(capability)
        if state.state is not PredictionFreezeStateV1.LABEL_ACCESS_AUTHORIZED:
            _fail("LABEL_CAPABILITY_NOT_AUTHORIZED")
        if state.authority_hash != expected_authority_hash:
            _fail("LABEL_CAPABILITY_AUTHORITY_MISMATCH")
        if state.source_commit != expected_source_commit:
            _fail("LABEL_CAPABILITY_SOURCE_COMMIT_MISMATCH")
        _verify_bound_bytes(state)
        return state.prediction_bytes_sha256


def consume_label_access_capability_v1(capability: LabelAccessCapabilityV1, label_reader: Callable[[], _T]) -> _T:
    if not callable(label_reader):
        _fail("LABEL_READER_NOT_CALLABLE")
    with _CAPABILITY_LOCK:
        state = _capability_state(capability)
        if state.state is not PredictionFreezeStateV1.LABEL_ACCESS_AUTHORIZED:
            _fail("LABEL_CAPABILITY_ALREADY_CONSUMED")
        _verify_bound_bytes(state)
        state.state = PredictionFreezeStateV1.LABEL_ACCESS_CONSUMED
    try:
        return label_reader()
    finally:
        _verify_bound_bytes(state)


def verify_prediction_unchanged_v1(capability: LabelAccessCapabilityV1) -> str:
    with _CAPABILITY_LOCK:
        state = _capability_state(capability)
        if state.state is not PredictionFreezeStateV1.LABEL_ACCESS_CONSUMED:
            _fail("POST_METRIC_VERIFY_OUT_OF_ORDER")
        _verify_bound_bytes(state)
        state.state = PredictionFreezeStateV1.POST_METRIC_VERIFIED
        return state.prediction_bytes_sha256


__all__ = [
    "D1PredictionRecordV2", "D1PredictionArtifactV2", "DurablePredictionFreezeReceiptV1",
    "LabelAccessCapabilityV1", "PredictionFreezeStateV1", "PredictionCustodyError",
    "persist_prediction_before_label_v1", "validate_prediction_document_v1",
    "authorize_label_access_v1", "consume_label_access_capability_v1", "verify_prediction_unchanged_v1",
    "validate_label_access_capability_v1",
]
