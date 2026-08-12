"""Transactional hash-chain custody for TASK-039E3 recovery V3.

The V2 JSONL ledgers could leave a complete-looking tail record after a
durability failure even though the in-memory head had not advanced.  This
module removes that ambiguity: immutable record files are data, while the
self-hashed ``HEAD.json`` document is the sole authoritative commit pointer.
An immutable record that is not reachable from ``HEAD.json`` is always an
``orphan_non_authoritative`` record.

The implementation deliberately supports one writer.  It performs no
provider, credential, or scientific-data access.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from threading import Lock
from typing import Any, Callable, Mapping

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    normalize_plain_json_v1,
)


SCHEMA_VERSION = "1.0.0"
RECORD_ARTIFACT_TYPE = "task039e3_transactional_custody_record_v3"
HEAD_ARTIFACT_TYPE = "task039e3_transactional_custody_head_v3"
LEDGER_ARTIFACT_TYPE = "task039e3_transactional_custody_ledger_v3"
HEAD_FILENAME = "HEAD.json"
LEDGER_FILENAME = "LEDGER.json"
RECORDS_DIRECTORY = "records"
PENDING_DIRECTORY = "pending"
ORPHAN_CLASSIFICATION = "orphan_non_authoritative"
HEAD_AUTHORITY = "sole_authoritative_committed_head"

FAULT_STAGES = (
    "candidate_write",
    "candidate_flush",
    "candidate_fsync",
    "record_promotion",
    "records_directory_fsync",
    "head_temp_write",
    "head_temp_flush",
    "head_temp_fsync",
    "head_replace",
    "ledger_directory_fsync",
    "disk_verification",
)


class TASK039E3TransactionalCustodyV3Error(RuntimeError):
    """Raised when transactional custody cannot prove a committed append."""


class TransactionalCustodyAppendV3Error(TASK039E3TransactionalCustodyV3Error):
    """Append failed without advancing the authoritative committed head."""

    def __init__(
        self,
        *,
        failed_stage: str,
        authoritative_head_hash: str | None,
        candidate_record_hash: str,
        candidate_classification: str,
    ) -> None:
        super().__init__(f"transactional custody append failed at {failed_stage}")
        self.failed_stage = failed_stage
        self.authoritative_head_hash = authoritative_head_hash
        self.candidate_record_hash = candidate_record_hash
        self.candidate_classification = candidate_classification


class TransactionalCustodyDoubleFaultV3Error(
    TASK039E3TransactionalCustodyV3Error
):
    """HEAD replacement failed and the previous committed HEAD could not restore."""


FaultInjectorV3 = Callable[[str, Mapping[str, Any]], None]
DirectorySyncV3 = Callable[[Path], None]


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):
        raise TASK039E3TransactionalCustodyV3Error(
            "transactional custody document must be a JSON object"
        )
    return (
        json.dumps(
            normalized,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _self_hashed(document: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):
        raise TASK039E3TransactionalCustodyV3Error(
            "transactional custody document must be a JSON object"
        )
    normalized.pop("artifact_hash", None)
    return {**normalized, "artifact_hash": stable_hash_v1(normalized)}


def _verify_self_hash(document: Mapping[str, Any], *, label: str) -> dict[str, Any]:
    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):
        raise TASK039E3TransactionalCustodyV3Error(f"{label} must be an object")
    observed = normalized.pop("artifact_hash", None)
    expected = stable_hash_v1(normalized)
    if observed != expected:
        raise TASK039E3TransactionalCustodyV3Error(f"{label} self-hash differs")
    return {**normalized, "artifact_hash": expected}


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TASK039E3TransactionalCustodyV3Error(
            f"{label} is unavailable or invalid"
        ) from exc
    if not isinstance(document, dict):
        raise TASK039E3TransactionalCustodyV3Error(f"{label} must be an object")
    return document


def _default_directory_sync(path: Path) -> None:
    """Fsync a directory when the platform exposes directory descriptors."""

    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write_without_faults(
    destination: Path,
    document: Mapping[str, Any],
    *,
    directory_sync: DirectorySyncV3,
) -> None:
    encoded = _canonical_bytes(document)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        directory_sync(destination.parent)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _record_content(
    *,
    ledger_kind: str,
    sequence_index: int,
    previous_record_hash: str | None,
    logical_call_kind: str,
    slot_identity: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_payload = normalize_plain_json_v1(payload)
    if not isinstance(normalized_payload, dict):
        raise TASK039E3TransactionalCustodyV3Error("record payload must be an object")
    return {
        "artifact_type": RECORD_ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "ledger_kind": ledger_kind,
        "sequence_index": sequence_index,
        "previous_record_hash": previous_record_hash,
        "logical_call_kind": logical_call_kind,
        "slot_identity": slot_identity,
        "payload": normalized_payload,
    }


def _finalize_record(content: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_plain_json_v1(content)
    if not isinstance(normalized, dict):
        raise TASK039E3TransactionalCustodyV3Error("record must be an object")
    normalized.pop("record_hash", None)
    return {**normalized, "record_hash": stable_hash_v1(normalized)}


def _verify_record(document: Mapping[str, Any], *, ledger_kind: str) -> dict[str, Any]:
    normalized = normalize_plain_json_v1(document)
    if not isinstance(normalized, dict):
        raise TASK039E3TransactionalCustodyV3Error("record must be an object")
    observed = normalized.pop("record_hash", None)
    expected = stable_hash_v1(normalized)
    if observed != expected:
        raise TASK039E3TransactionalCustodyV3Error("record hash differs")
    if normalized.get("artifact_type") != RECORD_ARTIFACT_TYPE:
        raise TASK039E3TransactionalCustodyV3Error("record artifact type differs")
    if normalized.get("schema_version") != SCHEMA_VERSION:
        raise TASK039E3TransactionalCustodyV3Error("record schema differs")
    if normalized.get("ledger_kind") != ledger_kind:
        raise TASK039E3TransactionalCustodyV3Error("record ledger kind differs")
    return {**normalized, "record_hash": expected}


def _ledger_hash(ledger_kind: str, records: tuple[Mapping[str, Any], ...]) -> str:
    return stable_hash_v1(
        {
            "artifact_type": LEDGER_ARTIFACT_TYPE,
            "ledger_kind": ledger_kind,
            "record_hashes": [record["record_hash"] for record in records],
        }
    )


def _head_document(
    *, ledger_kind: str, records: tuple[Mapping[str, Any], ...]
) -> dict[str, Any]:
    head_hash = records[-1]["record_hash"] if records else None
    return _self_hashed(
        {
            "artifact_type": HEAD_ARTIFACT_TYPE,
            "schema_version": SCHEMA_VERSION,
            "ledger_kind": ledger_kind,
            "head_authority": HEAD_AUTHORITY,
            "head_record_hash": head_hash,
            "record_count": len(records),
            "ledger_hash": _ledger_hash(ledger_kind, records),
        }
    )


@dataclass(frozen=True)
class TransactionalLedgerReconstructionV3:
    ledger_kind: str
    head_record_hash: str | None
    ledger_hash: str
    reachable_records: tuple[Mapping[str, Any], ...]
    orphan_records: tuple[Mapping[str, Any], ...]
    pending_files: tuple[str, ...]

    @property
    def authoritative_record_count(self) -> int:
        return len(self.reachable_records)

    @property
    def orphan_record_hashes(self) -> tuple[str, ...]:
        return tuple(str(record["record_hash"]) for record in self.orphan_records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_kind": self.ledger_kind,
            "head_authority": HEAD_AUTHORITY,
            "head_record_hash": self.head_record_hash,
            "ledger_hash": self.ledger_hash,
            "authoritative_record_count": self.authoritative_record_count,
            "reachable_record_hashes": [
                record["record_hash"] for record in self.reachable_records
            ],
            "orphan_records": [
                {
                    "record_hash": record["record_hash"],
                    "classification": ORPHAN_CLASSIFICATION,
                }
                for record in self.orphan_records
            ],
            "pending_files": list(self.pending_files),
        }


def reconstruct_transactional_ledger_v3(
    root: str | os.PathLike[str], *, ledger_kind: str
) -> TransactionalLedgerReconstructionV3:
    """Independently reconstruct only the chain reachable from ``HEAD.json``."""

    ledger_root = Path(root)
    metadata = _verify_self_hash(
        _read_json_object(ledger_root / LEDGER_FILENAME, label="LEDGER.json"),
        label="LEDGER.json",
    )
    if metadata.get("artifact_type") != LEDGER_ARTIFACT_TYPE:
        raise TASK039E3TransactionalCustodyV3Error("ledger artifact type differs")
    if metadata.get("ledger_kind") != ledger_kind:
        raise TASK039E3TransactionalCustodyV3Error("ledger kind differs")
    if metadata.get("head_authority") != HEAD_AUTHORITY:
        raise TASK039E3TransactionalCustodyV3Error("ledger head authority differs")

    head = _verify_self_hash(
        _read_json_object(ledger_root / HEAD_FILENAME, label="HEAD.json"),
        label="HEAD.json",
    )
    if head.get("artifact_type") != HEAD_ARTIFACT_TYPE:
        raise TASK039E3TransactionalCustodyV3Error("head artifact type differs")
    if head.get("ledger_kind") != ledger_kind:
        raise TASK039E3TransactionalCustodyV3Error("head ledger kind differs")
    if head.get("head_authority") != HEAD_AUTHORITY:
        raise TASK039E3TransactionalCustodyV3Error("head authority differs")

    records_path = ledger_root / RECORDS_DIRECTORY
    all_records: dict[str, dict[str, Any]] = {}
    if not records_path.is_dir():
        raise TASK039E3TransactionalCustodyV3Error("records directory is absent")
    for path in sorted(records_path.glob("*.json")):
        record = _verify_record(
            _read_json_object(path, label="transactional record"),
            ledger_kind=ledger_kind,
        )
        record_hash = str(record["record_hash"])
        if path.name != f"{int(record['sequence_index']):08d}-{record_hash}.json":
            raise TASK039E3TransactionalCustodyV3Error("record filename differs")
        if record_hash in all_records:
            raise TASK039E3TransactionalCustodyV3Error("duplicate record hash")
        all_records[record_hash] = record

    reachable_reverse: list[dict[str, Any]] = []
    cursor = head.get("head_record_hash")
    visited: set[str] = set()
    while cursor is not None:
        if not isinstance(cursor, str) or cursor in visited:
            raise TASK039E3TransactionalCustodyV3Error("record chain cycles or differs")
        record = all_records.get(cursor)
        if record is None:
            raise TASK039E3TransactionalCustodyV3Error("HEAD references absent record")
        visited.add(cursor)
        reachable_reverse.append(record)
        cursor = record.get("previous_record_hash")
    reachable = tuple(reversed(reachable_reverse))
    for index, record in enumerate(reachable):
        if record.get("sequence_index") != index:
            raise TASK039E3TransactionalCustodyV3Error("record sequence differs")
        expected_previous = reachable[index - 1]["record_hash"] if index else None
        if record.get("previous_record_hash") != expected_previous:
            raise TASK039E3TransactionalCustodyV3Error("record predecessor differs")

    observed_ledger_hash = _ledger_hash(ledger_kind, reachable)
    if head.get("record_count") != len(reachable):
        raise TASK039E3TransactionalCustodyV3Error("HEAD record count differs")
    if head.get("ledger_hash") != observed_ledger_hash:
        raise TASK039E3TransactionalCustodyV3Error("HEAD ledger hash differs")
    expected_head = reachable[-1]["record_hash"] if reachable else None
    if head.get("head_record_hash") != expected_head:
        raise TASK039E3TransactionalCustodyV3Error("HEAD record hash differs")

    orphans = tuple(
        record for key, record in sorted(all_records.items()) if key not in visited
    )
    pending_path = ledger_root / PENDING_DIRECTORY
    pending_files = (
        tuple(path.name for path in sorted(pending_path.iterdir()) if path.is_file())
        if pending_path.is_dir()
        else ()
    )
    return TransactionalLedgerReconstructionV3(
        ledger_kind=ledger_kind,
        head_record_hash=expected_head,
        ledger_hash=observed_ledger_hash,
        reachable_records=reachable,
        orphan_records=orphans,
        pending_files=pending_files,
    )


class TransactionalHashChainCustodyV3:
    """Single-writer transactional immutable-record custody.

    ``append`` updates in-memory state only after the new ``HEAD.json`` has
    survived its directory durability step and the complete disk chain has
    independently reconstructed.
    """

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        ledger_kind: str,
        allowed_logical_call_kind: str | None = None,
        fault_injector: FaultInjectorV3 | None = None,
        directory_sync: DirectorySyncV3 | None = None,
    ) -> None:
        if not isinstance(ledger_kind, str) or not ledger_kind:
            raise TASK039E3TransactionalCustodyV3Error("ledger kind is required")
        if allowed_logical_call_kind is not None and not allowed_logical_call_kind:
            raise TASK039E3TransactionalCustodyV3Error(
                "allowed logical-call kind must be non-empty"
            )
        self._root = Path(root)
        self._ledger_kind = ledger_kind
        self._allowed_logical_call_kind = allowed_logical_call_kind
        self._fault_injector = fault_injector
        self._directory_sync = directory_sync or _default_directory_sync
        self._write_lock = Lock()
        self._records_path = self._root / RECORDS_DIRECTORY
        self._pending_path = self._root / PENDING_DIRECTORY
        self._head_path = self._root / HEAD_FILENAME
        self._ledger_path = self._root / LEDGER_FILENAME

        if self._root.exists() and not self._root.is_dir():
            raise TASK039E3TransactionalCustodyV3Error("ledger root is not a directory")
        self._root.mkdir(parents=True, exist_ok=True)
        present = tuple(self._root.iterdir())
        if not present:
            self._initialize()
        elif not (
            self._records_path.is_dir()
            and self._pending_path.is_dir()
            and self._head_path.is_file()
            and self._ledger_path.is_file()
        ):
            raise TASK039E3TransactionalCustodyV3Error(
                "ledger root is neither empty nor a complete V3 ledger"
            )

        reconstructed = reconstruct_transactional_ledger_v3(
            self._root, ledger_kind=self._ledger_kind
        )
        self._records = list(reconstructed.reachable_records)
        self._head_hash = reconstructed.head_record_hash
        self._slot_identities = {
            str(record["slot_identity"]) for record in self._records
        }

    def _initialize(self) -> None:
        self._records_path.mkdir()
        self._pending_path.mkdir()
        metadata = _self_hashed(
            {
                "artifact_type": LEDGER_ARTIFACT_TYPE,
                "schema_version": SCHEMA_VERSION,
                "ledger_kind": self._ledger_kind,
                "head_authority": HEAD_AUTHORITY,
                "record_storage": "immutable_per_record_files",
                "unreachable_record_classification": ORPHAN_CLASSIFICATION,
                "single_authoritative_writer": True,
            }
        )
        _atomic_write_without_faults(
            self._ledger_path, metadata, directory_sync=self._directory_sync
        )
        _atomic_write_without_faults(
            self._head_path,
            _head_document(ledger_kind=self._ledger_kind, records=()),
            directory_sync=self._directory_sync,
        )

    @property
    def root(self) -> Path:
        return self._root

    @property
    def ledger_kind(self) -> str:
        return self._ledger_kind

    @property
    def records(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self._records)

    @property
    def authoritative_head_hash(self) -> str | None:
        return self._head_hash

    @property
    def authoritative_record_count(self) -> int:
        return len(self._records)

    @property
    def ledger_hash(self) -> str:
        return _ledger_hash(self._ledger_kind, tuple(self._records))

    def reconstruct(self) -> TransactionalLedgerReconstructionV3:
        return reconstruct_transactional_ledger_v3(
            self._root, ledger_kind=self._ledger_kind
        )

    def _inject(self, stage: str, context: Mapping[str, Any]) -> None:
        if stage not in FAULT_STAGES:
            raise TASK039E3TransactionalCustodyV3Error("unknown fault stage")
        if self._fault_injector is not None:
            self._fault_injector(stage, context)

    def _restore_previous_head(self, prior_head_bytes: bytes) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".HEAD.rollback.", suffix=".tmp", dir=str(self._root)
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(prior_head_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._head_path)
            self._directory_sync(self._root)
        except BaseException as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise TransactionalCustodyDoubleFaultV3Error(
                "previous authoritative HEAD restoration failed"
            ) from exc

    def append(
        self,
        *,
        logical_call_kind: str,
        slot_identity: str,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Durably append one immutable record and atomically advance HEAD."""

        if not self._write_lock.acquire(blocking=False):
            raise TASK039E3TransactionalCustodyV3Error(
                "concurrent transactional custody writers are prohibited"
            )
        try:
            if not isinstance(logical_call_kind, str) or not logical_call_kind:
                raise TASK039E3TransactionalCustodyV3Error(
                    "logical-call kind is required"
                )
            if (
                self._allowed_logical_call_kind is not None
                and logical_call_kind != self._allowed_logical_call_kind
            ):
                raise TASK039E3TransactionalCustodyV3Error(
                    "logical-call kind differs from ledger contract"
                )
            if not isinstance(slot_identity, str) or not slot_identity:
                raise TASK039E3TransactionalCustodyV3Error("slot identity is required")
            if slot_identity in self._slot_identities:
                raise TASK039E3TransactionalCustodyV3Error(
                    "slot identity was already committed"
                )

            content = _record_content(
                ledger_kind=self._ledger_kind,
                sequence_index=len(self._records),
                previous_record_hash=self._head_hash,
                logical_call_kind=logical_call_kind,
                slot_identity=slot_identity,
                payload=payload,
            )
            record = _finalize_record(content)
            record_hash = str(record["record_hash"])
            record_name = f"{len(self._records):08d}-{record_hash}.json"
            pending = self._pending_path / f"{record_name}.pending"
            destination = self._records_path / record_name
            if pending.exists() or destination.exists():
                raise TASK039E3TransactionalCustodyV3Error(
                    "transactional record path already exists"
                )

            context = {
                "ledger_kind": self._ledger_kind,
                "record_hash": record_hash,
                "previous_head_hash": self._head_hash,
            }
            prior_head_bytes = self._head_path.read_bytes()
            head_temporary: Path | None = None
            record_promoted = False
            head_replaced = False
            failed_stage = "candidate_write"
            try:
                encoded_record = _canonical_bytes(record)
                with pending.open("xb") as handle:
                    handle.write(encoded_record)
                    failed_stage = "candidate_write"
                    self._inject(failed_stage, context)
                    handle.flush()
                    failed_stage = "candidate_flush"
                    self._inject(failed_stage, context)
                    os.fsync(handle.fileno())
                    failed_stage = "candidate_fsync"
                    self._inject(failed_stage, context)

                os.replace(pending, destination)
                record_promoted = True
                failed_stage = "record_promotion"
                self._inject(failed_stage, context)
                self._directory_sync(self._records_path)
                failed_stage = "records_directory_fsync"
                self._inject(failed_stage, context)

                candidate_records = tuple([*self._records, record])
                head_document = _head_document(
                    ledger_kind=self._ledger_kind, records=candidate_records
                )
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=".HEAD.", suffix=".tmp", dir=str(self._root)
                )
                head_temporary = Path(temporary_name)
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(_canonical_bytes(head_document))
                    failed_stage = "head_temp_write"
                    self._inject(failed_stage, context)
                    handle.flush()
                    failed_stage = "head_temp_flush"
                    self._inject(failed_stage, context)
                    os.fsync(handle.fileno())
                    failed_stage = "head_temp_fsync"
                    self._inject(failed_stage, context)

                os.replace(head_temporary, self._head_path)
                head_temporary = None
                head_replaced = True
                failed_stage = "head_replace"
                self._inject(failed_stage, context)
                self._directory_sync(self._root)
                failed_stage = "ledger_directory_fsync"
                self._inject(failed_stage, context)

                reconstructed = reconstruct_transactional_ledger_v3(
                    self._root, ledger_kind=self._ledger_kind
                )
                failed_stage = "disk_verification"
                self._inject(failed_stage, context)
                if (
                    reconstructed.head_record_hash != record_hash
                    or reconstructed.authoritative_record_count
                    != len(candidate_records)
                    or reconstructed.orphan_record_hashes
                ):
                    raise TASK039E3TransactionalCustodyV3Error(
                        "new committed disk chain did not verify"
                    )

                # Commit in memory only after durable HEAD and disk verification.
                self._records.append(record)
                self._head_hash = record_hash
                self._slot_identities.add(slot_identity)
                return record
            except BaseException as exc:
                if head_replaced:
                    self._restore_previous_head(prior_head_bytes)
                try:
                    pending.unlink(missing_ok=True)
                except OSError:
                    pass
                if head_temporary is not None:
                    try:
                        head_temporary.unlink(missing_ok=True)
                    except OSError:
                        pass
                if isinstance(exc, TransactionalCustodyDoubleFaultV3Error):
                    raise
                classification = (
                    ORPHAN_CLASSIFICATION if record_promoted else "candidate_not_committed"
                )
                raise TransactionalCustodyAppendV3Error(
                    failed_stage=failed_stage,
                    authoritative_head_hash=self._head_hash,
                    candidate_record_hash=record_hash,
                    candidate_classification=classification,
                ) from exc
        finally:
            self._write_lock.release()


__all__ = [
    "FAULT_STAGES",
    "HEAD_AUTHORITY",
    "HEAD_FILENAME",
    "LEDGER_FILENAME",
    "ORPHAN_CLASSIFICATION",
    "PENDING_DIRECTORY",
    "RECORDS_DIRECTORY",
    "TASK039E3TransactionalCustodyV3Error",
    "TransactionalCustodyAppendV3Error",
    "TransactionalCustodyDoubleFaultV3Error",
    "TransactionalHashChainCustodyV3",
    "TransactionalLedgerReconstructionV3",
    "reconstruct_transactional_ledger_v3",
]
