"""Session-scoped, one-open sharing for authorized HAI feature frames.

The session is a compute-lifecycle optimization only.  It validates every
consumer operation before the split is opened, keeps the parsed frame private,
and shares immutable projections inside one process.  It provides no labels,
test2, outer, held-out, persistent cache, or scientific policy authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Sequence

from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER

from .hai_feature_adapter_v1 import (
    HAIFeatureAccessLedgerV1,
    HAIFeatureFrameV1,
    HAIFeatureReadReceiptV1,
    HAIFeatureRootCapabilityV1,
    load_authorized_hai_feature_frame_for_operations_v1,
)
from .protocol_v1 import ProtocolExecutionGuardV1, ProtocolOperationV1


class HAISharedFeatureSessionError(RuntimeError):
    """Path-free fail-closed shared-session error."""


_TOKEN = re.compile(r"[A-Z0-9][A-Z0-9_.:-]{0,95}\Z")
_FEATURE_ORDER = tuple(P1_FEATURE_ORDER)


def _fail(code: str) -> None:
    raise HAISharedFeatureSessionError(code)


def _canonical_bytes(document: dict[str, Any]) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _require_token(value: str, code: str) -> None:
    if type(value) is not str or _TOKEN.fullmatch(value) is None:
        _fail(code)


@dataclass(frozen=True)
class HAISharedFeatureConsumerV1:
    """One named consumer and its already-frozen protocol operation."""

    consumer_id: str
    operation: ProtocolOperationV1

    def __post_init__(self) -> None:
        _require_token(self.consumer_id, "SHARED_CONSUMER_ID_REJECTED")
        if type(self.operation) is not ProtocolOperationV1:
            _fail("SHARED_CONSUMER_OPERATION_REJECTED")

    def to_dict(self) -> dict[str, str]:
        return {
            "consumer_id": self.consumer_id,
            "operation": self.operation.value,
        }


class HAISharedFeatureSessionV1:
    """Open each authorized split once and share immutable projections."""

    __slots__ = (
        "_experiment_id",
        "_capability",
        "_protocol_guard",
        "_ledger",
        "_frames",
        "_consumers",
        "_projection_cache",
        "_projection_count",
        "_records",
        "_closed",
    )

    def __init__(
        self,
        *,
        experiment_id: str,
        capability: HAIFeatureRootCapabilityV1,
        protocol_guard: ProtocolExecutionGuardV1,
    ) -> None:
        _require_token(experiment_id, "SHARED_EXPERIMENT_ID_REJECTED")
        if type(capability) is not HAIFeatureRootCapabilityV1:
            _fail("SHARED_ROOT_CAPABILITY_REJECTED")
        if type(protocol_guard) is not ProtocolExecutionGuardV1:
            _fail("SHARED_PROTOCOL_GUARD_REJECTED")
        self._experiment_id = experiment_id
        self._capability = capability
        self._protocol_guard = protocol_guard
        self._ledger = HAIFeatureAccessLedgerV1(experiment_id=experiment_id)
        self._frames: dict[str, HAIFeatureFrameV1] = {}
        self._consumers: dict[tuple[str, str], HAISharedFeatureConsumerV1] = {}
        self._projection_cache: dict[tuple[str, tuple[str, ...]], Any] = {}
        self._projection_count = 0
        self._records: dict[str, dict[str, Any]] = {}
        self._closed = False

    def __repr__(self) -> str:
        return "HAISharedFeatureSessionV1(<private frames redacted>)"

    def __reduce__(self) -> Any:
        _fail("SHARED_SESSION_SERIALIZATION_REJECTED")

    def __enter__(self) -> "HAISharedFeatureSessionV1":
        self._require_open()
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self.close()

    def _require_open(self) -> None:
        if self._closed:
            _fail("SHARED_SESSION_CLOSED")

    def open_split(
        self,
        *,
        split_id: str,
        consumers: tuple[HAISharedFeatureConsumerV1, ...],
    ) -> HAIFeatureReadReceiptV1:
        """Validate all consumers and materialize one immutable source frame."""

        self._require_open()
        if type(split_id) is not str or not split_id:
            _fail("SHARED_SPLIT_ID_REJECTED")
        if split_id in self._frames:
            _fail("SHARED_SPLIT_ALREADY_OPEN")
        if (
            type(consumers) is not tuple
            or not consumers
            or any(type(item) is not HAISharedFeatureConsumerV1 for item in consumers)
        ):
            _fail("SHARED_CONSUMER_SET_REJECTED")
        consumer_ids = tuple(item.consumer_id for item in consumers)
        if len(consumer_ids) != len(set(consumer_ids)):
            _fail("SHARED_CONSUMER_DUPLICATE_REJECTED")

        operations = tuple(
            sorted({item.operation for item in consumers}, key=lambda item: item.value)
        )
        frame = load_authorized_hai_feature_frame_for_operations_v1(
            capability=self._capability,
            split_id=split_id,
            operations=operations,
            protocol_guard=self._protocol_guard,
            ledger=self._ledger,
        )

        self._frames[split_id] = frame
        for consumer in consumers:
            self._consumers[(split_id, consumer.consumer_id)] = consumer
        source = frame.receipt.to_dict()
        self._records[split_id] = {
            "split_id": split_id,
            "operations": [item.value for item in operations],
            "consumers": [item.to_dict() for item in sorted(consumers, key=lambda item: item.consumer_id)],
            "source_receipt_hash": source["receipt_hash"],
            "source_file_open_count": source["file_open_count"],
        }
        return frame.receipt

    def numeric_matrix(
        self,
        *,
        split_id: str,
        consumer_id: str,
        feature_ids: Sequence[str] = _FEATURE_ORDER,
    ) -> Any:
        """Return one cached immutable projection to a registered consumer."""

        self._require_open()
        _require_token(consumer_id, "SHARED_CONSUMER_ID_REJECTED")
        if (split_id, consumer_id) not in self._consumers:
            _fail("SHARED_CONSUMER_NOT_AUTHORIZED")
        requested = tuple(feature_ids)
        key = (split_id, requested)
        if key not in self._projection_cache:
            matrix = self._frames[split_id].numeric_matrix(requested)
            if bool(matrix.flags.writeable):
                _fail("SHARED_PROJECTION_MUTABLE_REJECTED")
            self._projection_cache[key] = matrix
            self._projection_count += 1
        result = self._projection_cache[key].view()
        result.setflags(write=False)
        return result

    def file_local_timestamps(self, *, split_id: str, consumer_id: str) -> tuple[str, ...]:
        """Return the immutable file-local coordinate after consumer admission."""

        self._require_open()
        _require_token(consumer_id, "SHARED_CONSUMER_ID_REJECTED")
        if (split_id, consumer_id) not in self._consumers:
            _fail("SHARED_CONSUMER_NOT_AUTHORIZED")
        return self._frames[split_id].file_local_timestamps()

    def public_document(self) -> dict[str, Any]:
        """Return a path-free receipt; never serialize frames or numeric values."""

        ledger = self._ledger.public_document()
        body = {
            "schema": "paperworks.validation_v2.hai_shared_feature_session_v1",
            "schema_version": "1.0.0",
            "experiment_id": self._experiment_id,
            "state": "CLOSED" if self._closed else "OPEN",
            "split_records": [self._records[key] for key in sorted(self._records)],
            "feature_file_open_count": ledger["feature_file_open_count"],
            "opened_split_ids": ledger["opened_split_ids"],
            "unique_projection_count": self._projection_count,
            "persistent_cache_created": False,
            "labels_accessed": False,
            "test1_feature_accesses": int("test1" in ledger["opened_split_ids"]),
            "test2_accesses": 0,
            "heldout_accesses": 0,
            "private_paths_embedded": False,
            "numeric_values_embedded": False,
        }
        document = dict(body)
        document["receipt_hash"] = sha256(_canonical_bytes(body)).hexdigest()
        return document

    def close(self) -> None:
        """Release session-owned references without persisting scientific data."""

        if self._closed:
            return
        self._projection_cache.clear()
        self._frames.clear()
        self._closed = True


__all__ = [
    "HAISharedFeatureConsumerV1",
    "HAISharedFeatureSessionError",
    "HAISharedFeatureSessionV1",
]
