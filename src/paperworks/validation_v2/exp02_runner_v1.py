"""Fail-closed execution shell for Validation V2 EXP-02.

The scientific algorithms needed to produce relation-local summaries and
train4 opportunity censuses are intentionally *not* implemented here.  This
module accepts those algorithms only after three separately versioned binding
receipts have been frozen outside the runner and replay against caller-supplied
hashes.  No split opener can run before that replay succeeds.

The module also provides public-safe custody receipts, exact 37-candidate
closure, and an immutable atomic persistence adapter for the selected-policy
payload produced by :mod:`exp02_scientific_v1`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any, BinaryIO, Callable, Mapping, Sequence, TypeVar
from uuid import uuid4

from .exp02_scientific_v1 import (
    AtomicFreezeEvidenceV1,
    CandidateSetFreezeReceiptV1,
    Exp02OperationV1,
    Exp02ScientificError,
    FormalV4NumericAuthorityPublicReceiptV1,
    PrivateSummaryHashReceiptV1,
    SelectedPolicyFreezeReceiptV1,
    SelectionDecisionReceiptV1,
    V2ConfirmedCohortBindingV1,
    assert_exp02_split_allowed_v1,
    build_atomic_freeze_evidence_v1,
    build_candidate_set_freeze_receipt_v1,
    freeze_selected_policy_v1,
    validate_private_summary_hash_receipts_v1,
    validate_v2_confirmed_cohort_binding_v1,
)
from .numeric_policy_v1 import (
    ConfirmedCohortAuthorityV1,
    NumericPolicyCandidateV1,
    build_numeric_policy_candidate_set_v1,
    candidate_set_hash_v1,
    validate_confirmed_cohort_authority_v1,
)


EXP02_RUNNER_VERSION = "VALIDATION_V2_EXP02_RUNNER_V1"
EXP02_REQUIRED_BINDING_IDS = (
    "EXP02-BIND-QUANTILE",
    "EXP02-BIND-RELATION-SUMMARY",
    "EXP02-BIND-OPPORTUNITY-CENSUS",
)
EXP02_FORBIDDEN_SPLITS = frozenset(
    ("test1", "test2", "heldout", "future_heldout", "outer", "sealed")
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_PUBLIC_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}$")
_T = TypeVar("_T")


class Exp02RunnerError(ValueError):
    """Stable fail-closed issue emitted by the EXP-02 runner shell."""

    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


def _fail(code: str, message: str) -> None:
    raise Exp02RunnerError(code, message)


def _canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(document), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _hash(document: Mapping[str, Any]) -> str:
    return sha256(_canonical_bytes(document)).hexdigest()


def _sha(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        _fail("EXP02_RUNNER_HASH_INVALID", f"{name} must be lowercase SHA-256")
    return value


def _commit(value: object) -> str:
    if type(value) is not str or _COMMIT.fullmatch(value) is None:
        _fail("EXP02_RUNNER_COMMIT_INVALID", "source_commit must be an exact Git commit")
    return value


def _public_id(value: object, name: str) -> str:
    if type(value) is not str or _PUBLIC_ID.fullmatch(value) is None:
        _fail("EXP02_RUNNER_PUBLIC_ID_INVALID", f"{name} must be a path-free public identifier")
    return value


@dataclass(frozen=True)
class FrozenScientificBindingV1:
    """Externally frozen identity for one unresolved scientific semantic."""

    binding_id: str
    contract_id: str
    specification_hash: str
    implementation_hash: str
    configuration_hash: str
    source_commit: str
    frozen_before_data_io: bool
    status: str
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_frozen_scientific_binding_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def build_frozen_scientific_binding_v1(
    *, binding_id: str, contract_id: str, specification_hash: str,
    implementation_hash: str, configuration_hash: str, source_commit: str,
) -> FrozenScientificBindingV1:
    if binding_id not in EXP02_REQUIRED_BINDING_IDS:
        _fail("EXP02_RUNNER_BINDING_ID_INVALID", "binding is outside the frozen three-item set")
    _public_id(contract_id, "contract_id")
    for name, value in (
        ("specification_hash", specification_hash),
        ("implementation_hash", implementation_hash),
        ("configuration_hash", configuration_hash),
    ):
        _sha(value, name)
    _commit(source_commit)
    provisional = FrozenScientificBindingV1(
        binding_id=binding_id, contract_id=contract_id,
        specification_hash=specification_hash,
        implementation_hash=implementation_hash,
        configuration_hash=configuration_hash, source_commit=source_commit,
        frozen_before_data_io=True, status="FROZEN", self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def frozen_scientific_binding_from_dict_v1(
    value: Mapping[str, Any],
) -> FrozenScientificBindingV1:
    if type(value) is not dict:
        _fail("EXP02_RUNNER_BINDING_DOCUMENT_INVALID", "binding document must be an exact object")
    expected_keys = {
        "artifact_type", "schema_version", "binding_id", "contract_id",
        "specification_hash", "implementation_hash", "configuration_hash",
        "source_commit", "frozen_before_data_io", "status", "self_hash",
    }
    if set(value) != expected_keys:
        _fail("EXP02_RUNNER_BINDING_DOCUMENT_INVALID", "binding document keys differ")
    if value["artifact_type"] != "validation_v2_exp02_frozen_scientific_binding_v1" or value["schema_version"] != "1.0.0":
        _fail("EXP02_RUNNER_BINDING_SCHEMA_INVALID", "binding schema identity differs")
    expected = build_frozen_scientific_binding_v1(
        binding_id=value["binding_id"], contract_id=value["contract_id"],
        specification_hash=value["specification_hash"],
        implementation_hash=value["implementation_hash"],
        configuration_hash=value["configuration_hash"],
        source_commit=value["source_commit"],
    )
    if value["frozen_before_data_io"] is not True or value["status"] != "FROZEN":
        _fail("EXP02_RUNNER_BINDING_NOT_FROZEN", "binding is not frozen before data I/O")
    if value["self_hash"] != expected.self_hash:
        _fail("EXP02_RUNNER_BINDING_REPLAY_MISMATCH", "binding differs from deterministic replay")
    return expected


@dataclass(frozen=True)
class ScientificBindingBundleReceiptV1:
    binding_hashes: tuple[tuple[str, str], ...]
    source_commit: str
    binding_count: int
    complete: bool
    data_io_authorized: bool
    labels_allowed: bool
    test1_allowed: bool
    test2_allowed: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_scientific_binding_bundle_receipt_v1",
            "binding_count": self.binding_count,
            "binding_hashes": [list(item) for item in self.binding_hashes],
            "complete": self.complete,
            "data_io_authorized": self.data_io_authorized,
            "labels_allowed": self.labels_allowed,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "test1_allowed": self.test1_allowed,
            "test2_allowed": self.test2_allowed,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def validate_scientific_binding_bundle_v1(
    bindings: Sequence[FrozenScientificBindingV1], *,
    expected_binding_hashes: Mapping[str, str], source_commit: str,
) -> ScientificBindingBundleReceiptV1:
    """Replay exact external bindings; this must run before any opener."""

    _commit(source_commit)
    if type(bindings) not in (tuple, list):
        _fail("EXP02_RUNNER_BINDING_BUNDLE_INVALID", "bindings must be an exact sequence")
    if set(expected_binding_hashes) != set(EXP02_REQUIRED_BINDING_IDS):
        _fail("EXP02_RUNNER_BINDING_EXPECTATION_INCOMPLETE", "all three external binding hashes are required")
    by_id: dict[str, FrozenScientificBindingV1] = {}
    for binding in bindings:
        if type(binding) is not FrozenScientificBindingV1 or binding.binding_id in by_id:
            _fail("EXP02_RUNNER_BINDING_BUNDLE_INVALID", "binding type differs or ID duplicates")
        expected = build_frozen_scientific_binding_v1(
            binding_id=binding.binding_id, contract_id=binding.contract_id,
            specification_hash=binding.specification_hash,
            implementation_hash=binding.implementation_hash,
            configuration_hash=binding.configuration_hash,
            source_commit=binding.source_commit,
        )
        if binding != expected or not binding.frozen_before_data_io or binding.status != "FROZEN":
            _fail("EXP02_RUNNER_BINDING_REPLAY_MISMATCH", "binding differs from replay")
        if binding.source_commit != source_commit:
            _fail("EXP02_RUNNER_BINDING_COMMIT_MISMATCH", "binding source commit differs")
        frozen_hash = expected_binding_hashes.get(binding.binding_id)
        if frozen_hash is None:
            _fail("EXP02_RUNNER_BINDING_SET_INCOMPLETE", "required binding is missing")
        _sha(frozen_hash, f"expected_{binding.binding_id}")
        if binding.self_hash != frozen_hash:
            _fail("EXP02_RUNNER_BINDING_STALE", "binding differs from external frozen identity")
        by_id[binding.binding_id] = binding
    if set(by_id) != set(EXP02_REQUIRED_BINDING_IDS):
        _fail("EXP02_RUNNER_BINDING_SET_INCOMPLETE", "exactly the three required bindings are required")
    ordered = tuple((name, by_id[name].self_hash) for name in EXP02_REQUIRED_BINDING_IDS)
    provisional = ScientificBindingBundleReceiptV1(
        binding_hashes=ordered, source_commit=source_commit,
        binding_count=len(ordered), complete=True, data_io_authorized=True,
        labels_allowed=False, test1_allowed=False, test2_allowed=False,
        self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


@dataclass(frozen=True)
class SplitOpenEventV1:
    ordinal: int
    split_id: str
    operation: str
    purpose_id: str
    byte_count: int
    content_sha256: str
    previous_event_hash: str | None
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


@dataclass(frozen=True)
class SplitOpenLedgerV1:
    binding_bundle_hash: str
    events: tuple[SplitOpenEventV1, ...]
    test1_accesses: int
    test2_accesses: int
    label_accesses: int
    heldout_accesses: int
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_split_open_ledger_v1",
            "binding_bundle_hash": self.binding_bundle_hash,
            "events": [item.to_dict() for item in self.events],
            "heldout_accesses": self.heldout_accesses,
            "label_accesses": self.label_accesses,
            "schema_version": "1.0.0",
            "test1_accesses": self.test1_accesses,
            "test2_accesses": self.test2_accesses,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def start_split_open_ledger_v1(
    binding_bundle: ScientificBindingBundleReceiptV1,
) -> SplitOpenLedgerV1:
    if type(binding_bundle) is not ScientificBindingBundleReceiptV1 or binding_bundle.self_hash != _hash(binding_bundle.body_dict()):
        _fail("EXP02_RUNNER_BINDING_RECEIPT_MUTATED", "binding bundle receipt differs")
    if not binding_bundle.complete or not binding_bundle.data_io_authorized:
        _fail("EXP02_RUNNER_DATA_IO_NOT_AUTHORIZED", "complete frozen bindings are required")
    provisional = SplitOpenLedgerV1(
        binding_bundle_hash=binding_bundle.self_hash, events=(), test1_accesses=0,
        test2_accesses=0, label_accesses=0, heldout_accesses=0, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


OpenCallbackV1 = Callable[[], tuple[_T, int, str]]


def execute_authorized_split_open_v1(
    *, binding_bundle: ScientificBindingBundleReceiptV1,
    ledger: SplitOpenLedgerV1, split_id: str, operation: Exp02OperationV1,
    purpose_id: str, opener: OpenCallbackV1[_T],
) -> tuple[_T, SplitOpenLedgerV1]:
    """Call a private opener only after binding and split-role validation."""

    if type(binding_bundle) is not ScientificBindingBundleReceiptV1 or binding_bundle.self_hash != _hash(binding_bundle.body_dict()):
        _fail("EXP02_RUNNER_BINDING_RECEIPT_MUTATED", "binding bundle receipt differs")
    if not binding_bundle.complete or not binding_bundle.data_io_authorized:
        _fail("EXP02_RUNNER_DATA_IO_NOT_AUTHORIZED", "complete frozen bindings are required")
    if type(ledger) is not SplitOpenLedgerV1 or ledger.self_hash != _hash(ledger.body_dict()):
        _fail("EXP02_RUNNER_OPEN_LEDGER_MUTATED", "split-open ledger differs from replay")
    if ledger.binding_bundle_hash != binding_bundle.self_hash:
        _fail("EXP02_RUNNER_OPEN_LEDGER_STALE", "ledger binds another binding bundle")
    if split_id.lower() in EXP02_FORBIDDEN_SPLITS:
        _fail("EXP02_RUNNER_SPLIT_PROHIBITED", "evaluation, held-out, and label splits are prohibited")
    try:
        assert_exp02_split_allowed_v1(split_id=split_id, operation=operation)
    except Exp02ScientificError as exc:
        _fail("EXP02_RUNNER_SPLIT_PROHIBITED", exc.message)
    _public_id(purpose_id, "purpose_id")
    if not callable(opener):
        _fail("EXP02_RUNNER_OPENER_INVALID", "private opener callback is required")
    payload, byte_count, content_hash = opener()
    if type(byte_count) is not int or byte_count <= 0:
        _fail("EXP02_RUNNER_OPEN_BYTE_COUNT_INVALID", "opener byte count must be positive")
    _sha(content_hash, "content_sha256")
    previous = None if not ledger.events else ledger.events[-1].self_hash
    provisional_event = SplitOpenEventV1(
        ordinal=len(ledger.events) + 1, split_id=split_id,
        operation=operation.value, purpose_id=purpose_id,
        byte_count=byte_count, content_sha256=content_hash,
        previous_event_hash=previous, self_hash="",
    )
    event = replace(provisional_event, self_hash=_hash(provisional_event.body_dict()))
    provisional = replace(ledger, events=ledger.events + (event,), self_hash="")
    updated = replace(provisional, self_hash=_hash(provisional.body_dict()))
    return payload, updated


@dataclass(frozen=True)
class CohortProjectionReceiptV1:
    candidate_policy_hash: str
    cohort_hash: str
    cohort_binding_hash: str
    projection_artifact_hash: str
    relation_ids_hash: str
    relation_count: int
    source_commit: str
    confirmation_split: str
    contains_private_paths: bool
    contains_numeric_values: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_cohort_projection_receipt_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def build_cohort_projection_receipt_v1(
    *, cohort: ConfirmedCohortAuthorityV1,
    cohort_binding: V2ConfirmedCohortBindingV1,
    candidate_policy_hash: str, projection_artifact_hash: str,
) -> CohortProjectionReceiptV1:
    validate_confirmed_cohort_authority_v1(cohort)
    validate_v2_confirmed_cohort_binding_v1(
        cohort_binding, cohort=cohort, expected_receipt_hash=cohort_binding.self_hash,
    )
    _sha(candidate_policy_hash, "candidate_policy_hash")
    _sha(projection_artifact_hash, "projection_artifact_hash")
    relation_ids_hash = _hash({"relation_ids": [item.relation_id for item in cohort.relations]})
    if relation_ids_hash != cohort_binding.relation_ids_hash:
        _fail("EXP02_RUNNER_PROJECTION_RELATION_MISMATCH", "projected relation IDs differ")
    provisional = CohortProjectionReceiptV1(
        candidate_policy_hash=candidate_policy_hash, cohort_hash=cohort.cohort_hash,
        cohort_binding_hash=cohort_binding.self_hash,
        projection_artifact_hash=projection_artifact_hash,
        relation_ids_hash=relation_ids_hash, relation_count=len(cohort.relations),
        source_commit=cohort.source_commit, confirmation_split=cohort.confirmation_split,
        contains_private_paths=False, contains_numeric_values=False, self_hash="",
    )
    return replace(provisional, self_hash=_hash(provisional.body_dict()))


def validate_cohort_projection_receipt_v1(
    receipt: CohortProjectionReceiptV1, *, cohort: ConfirmedCohortAuthorityV1,
    cohort_binding: V2ConfirmedCohortBindingV1, candidate_policy_hash: str,
    expected_receipt_hash: str,
) -> str:
    if type(receipt) is not CohortProjectionReceiptV1:
        _fail("EXP02_RUNNER_PROJECTION_TYPE_INVALID", "projection receipt type differs")
    expected = build_cohort_projection_receipt_v1(
        cohort=cohort, cohort_binding=cohort_binding,
        candidate_policy_hash=candidate_policy_hash,
        projection_artifact_hash=receipt.projection_artifact_hash,
    )
    if receipt != expected or receipt.contains_private_paths or receipt.contains_numeric_values:
        _fail("EXP02_RUNNER_PROJECTION_REPLAY_MISMATCH", "projection differs from replay")
    _sha(expected_receipt_hash, "expected_projection_receipt_hash")
    if receipt.self_hash != expected_receipt_hash:
        _fail("EXP02_RUNNER_PROJECTION_STALE", "projection differs from external identity")
    return receipt.self_hash


@dataclass(frozen=True)
class CandidateClosureReceiptV1:
    binding_bundle_hash: str
    projection_receipt_hash: str
    candidate_set_receipt_hash: str
    candidate_set_hash: str
    candidate_count: int
    common_candidate_count: int
    relation_specific_candidate_count: int
    closed_before_train4: bool
    test1_accesses: int
    test2_accesses: int
    label_accesses: int
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_candidate_closure_receipt_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


def close_exact_candidate_set_v1(
    *, binding_bundle: ScientificBindingBundleReceiptV1,
    projection: CohortProjectionReceiptV1,
    expected_projection_hash: str,
    cohort: ConfirmedCohortAuthorityV1,
    cohort_binding: V2ConfirmedCohortBindingV1,
    candidate_policy_hash: str,
    normal_fit_input_hash: str,
    summary_receipts: Sequence[PrivateSummaryHashReceiptV1],
    expected_summary_receipt_hashes: Mapping[str, str],
) -> tuple[tuple[NumericPolicyCandidateV1, ...], CandidateSetFreezeReceiptV1, CandidateClosureReceiptV1]:
    if type(binding_bundle) is not ScientificBindingBundleReceiptV1 or binding_bundle.self_hash != _hash(binding_bundle.body_dict()):
        _fail("EXP02_RUNNER_BINDING_RECEIPT_MUTATED", "binding bundle receipt differs")
    if not binding_bundle.complete or not binding_bundle.data_io_authorized:
        _fail("EXP02_RUNNER_DATA_IO_NOT_AUTHORIZED", "complete frozen bindings are required")
    validate_cohort_projection_receipt_v1(
        projection, cohort=cohort, cohort_binding=cohort_binding,
        candidate_policy_hash=candidate_policy_hash,
        expected_receipt_hash=expected_projection_hash,
    )
    fit_summary_hash = validate_private_summary_hash_receipts_v1(
        summary_receipts, cohort=cohort_binding,
        expected_receipt_hashes=expected_summary_receipt_hashes,
    )
    candidates = build_numeric_policy_candidate_set_v1(
        cohort=cohort, normal_fit_input_hash=normal_fit_input_hash,
        source_commit=cohort.source_commit,
    )
    if len(candidates) != 37:
        _fail("EXP02_RUNNER_CANDIDATE_CLOSURE_INCOMPLETE", "exactly 37 candidates are required")
    candidate_receipt = build_candidate_set_freeze_receipt_v1(
        candidates=candidates, cohort=cohort_binding,
        fit_summary_receipts_hash=fit_summary_hash,
    )
    common_count = sum(item.candidate_id == "COMMON_FIXED_NORMALIZED_V1" for item in candidates)
    relation_count = len(candidates) - common_count
    if common_count != 1 or relation_count != 36:
        _fail("EXP02_RUNNER_CANDIDATE_CLOSURE_INCOMPLETE", "candidate family cardinality differs")
    provisional = CandidateClosureReceiptV1(
        binding_bundle_hash=binding_bundle.self_hash,
        projection_receipt_hash=projection.self_hash,
        candidate_set_receipt_hash=candidate_receipt.self_hash,
        candidate_set_hash=candidate_set_hash_v1(candidates), candidate_count=37,
        common_candidate_count=1, relation_specific_candidate_count=36,
        closed_before_train4=True, test1_accesses=0, test2_accesses=0,
        label_accesses=0, self_hash="",
    )
    closure = replace(provisional, self_hash=_hash(provisional.body_dict()))
    return candidates, candidate_receipt, closure


@dataclass(frozen=True)
class AtomicPersistenceReceiptV1:
    artifact_id: str
    byte_count: int
    payload_sha256: str
    atomic_replace_completed: bool
    file_fsync_completed: bool
    close_completed: bool
    directory_fsync_completed: bool
    reopen_completed: bool
    temporary_removed: bool
    contains_private_path: bool
    self_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_exp02_atomic_persistence_receipt_v1",
            **{key: value for key, value in self.__dict__.items() if key != "self_hash"},
            "schema_version": "1.0.0",
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "self_hash": self.self_hash}


WritePayloadV1 = Callable[[BinaryIO, bytes], int]
FileFsyncV1 = Callable[[int], None]
AtomicReplaceV1 = Callable[[Path, Path], None]
DirectoryFsyncV1 = Callable[[Path], None]
ReopenReaderV1 = Callable[[Path], bytes]


def _default_write(handle: BinaryIO, payload: bytes) -> int:
    return handle.write(payload)


def _default_replace(source: Path, destination: Path) -> None:
    os.replace(source, destination)


def _default_reopen(path: Path) -> bytes:
    return path.read_bytes()


def _default_directory_fsync(directory: Path) -> None:
    if os.name == "nt":
        _fail(
            "EXP02_RUNNER_DIRECTORY_FSYNC_ADAPTER_REQUIRED",
            "Windows scientific freeze requires an explicitly verified directory-sync adapter",
        )
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_persist_selected_policy_v1(
    *, artifact_id: str, payload: bytes, target_path: Path,
    write_payload: WritePayloadV1 = _default_write,
    file_fsync: FileFsyncV1 = os.fsync,
    atomic_replace: AtomicReplaceV1 = _default_replace,
    directory_fsync: DirectoryFsyncV1 = _default_directory_fsync,
    reopen_reader: ReopenReaderV1 = _default_reopen,
) -> tuple[AtomicFreezeEvidenceV1, AtomicPersistenceReceiptV1]:
    """Persist one new private policy file and return only path-free evidence."""

    _public_id(artifact_id, "artifact_id")
    if type(payload) is not bytes or not payload:
        _fail("EXP02_RUNNER_FREEZE_PAYLOAD_INVALID", "payload must be non-empty exact bytes")
    if not isinstance(target_path, Path) or not target_path.is_absolute():
        _fail("EXP02_RUNNER_TARGET_PATH_INVALID", "private target must be an absolute Path")
    parent = target_path.parent
    if not parent.is_dir():
        _fail("EXP02_RUNNER_TARGET_PARENT_MISSING", "private target parent must already exist")
    if target_path.exists():
        _fail("EXP02_RUNNER_TARGET_EXISTS", "immutable selected-policy target already exists")
    temp_path = parent / f".{target_path.name}.{uuid4().hex}.tmp"
    handle: BinaryIO | None = None
    replaced = False
    try:
        handle = temp_path.open("x+b")
        written = write_payload(handle, payload)
        if type(written) is not int or written != len(payload):
            _fail("EXP02_RUNNER_PARTIAL_WRITE", "selected-policy payload was not written in full")
        handle.flush()
        file_fsync(handle.fileno())
        handle.close()
        handle = None
        atomic_replace(temp_path, target_path)
        replaced = True
        directory_fsync(parent)
        reopened = reopen_reader(target_path)
        if type(reopened) is not bytes:
            _fail("EXP02_RUNNER_REOPEN_TYPE_INVALID", "reopened selected policy must be exact bytes")
        payload_hash = sha256(payload).hexdigest()
        reopened_hash = sha256(reopened).hexdigest()
        if reopened_hash != payload_hash or reopened != payload:
            _fail("EXP02_RUNNER_REOPEN_MISMATCH", "reopened selected policy differs")
        evidence = build_atomic_freeze_evidence_v1(
            artifact_id=artifact_id, payload=payload,
            reopened_bytes_sha256=reopened_hash,
            atomic_replace_completed=True, fsync_completed=True,
            close_completed=True, reopen_completed=True,
        )
        provisional = AtomicPersistenceReceiptV1(
            artifact_id=artifact_id, byte_count=len(payload),
            payload_sha256=payload_hash, atomic_replace_completed=True,
            file_fsync_completed=True, close_completed=True,
            directory_fsync_completed=True, reopen_completed=True,
            temporary_removed=not temp_path.exists(), contains_private_path=False,
            self_hash="",
        )
        receipt = replace(provisional, self_hash=_hash(provisional.body_dict()))
        return evidence, receipt
    except Exp02RunnerError:
        raise
    except Exception as exc:
        _fail("EXP02_RUNNER_ATOMIC_PERSISTENCE_FAILED", type(exc).__name__)
    finally:
        if handle is not None:
            handle.close()
        if not replaced and temp_path.exists():
            temp_path.unlink()


def freeze_selected_policy_atomically_v1(
    *, artifact_id: str, decision: SelectionDecisionReceiptV1,
    numeric_authority: FormalV4NumericAuthorityPublicReceiptV1,
    target_path: Path, write_payload: WritePayloadV1 = _default_write,
    file_fsync: FileFsyncV1 = os.fsync,
    atomic_replace: AtomicReplaceV1 = _default_replace,
    directory_fsync: DirectoryFsyncV1 = _default_directory_fsync,
    reopen_reader: ReopenReaderV1 = _default_reopen,
) -> tuple[SelectedPolicyFreezeReceiptV1, AtomicPersistenceReceiptV1]:
    persistence: AtomicPersistenceReceiptV1 | None = None

    def persist(payload: bytes) -> AtomicFreezeEvidenceV1:
        nonlocal persistence
        evidence, persistence = atomic_persist_selected_policy_v1(
            artifact_id=artifact_id, payload=payload, target_path=target_path,
            write_payload=write_payload, file_fsync=file_fsync,
            atomic_replace=atomic_replace, directory_fsync=directory_fsync,
            reopen_reader=reopen_reader,
        )
        return evidence

    selected = freeze_selected_policy_v1(
        artifact_id=artifact_id, decision=decision,
        numeric_authority=numeric_authority, persist_and_reopen=persist,
    )
    if persistence is None:
        _fail("EXP02_RUNNER_ATOMIC_EVIDENCE_MISSING", "persistence callback produced no evidence")
    return selected, persistence


__all__ = [
    "EXP02_FORBIDDEN_SPLITS", "EXP02_REQUIRED_BINDING_IDS", "EXP02_RUNNER_VERSION",
    "AtomicPersistenceReceiptV1", "CandidateClosureReceiptV1",
    "CohortProjectionReceiptV1", "Exp02RunnerError", "FrozenScientificBindingV1",
    "ScientificBindingBundleReceiptV1", "SplitOpenEventV1", "SplitOpenLedgerV1",
    "atomic_persist_selected_policy_v1", "build_cohort_projection_receipt_v1",
    "build_frozen_scientific_binding_v1", "close_exact_candidate_set_v1",
    "execute_authorized_split_open_v1", "freeze_selected_policy_atomically_v1",
    "frozen_scientific_binding_from_dict_v1", "start_split_open_ledger_v1",
    "validate_cohort_projection_receipt_v1", "validate_scientific_binding_bundle_v1",
]
