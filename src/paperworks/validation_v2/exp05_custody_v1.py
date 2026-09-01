"""Durable, public-safe cohort custody for prospective EXP-05 evaluation.

Only hashes and opaque identifiers are persisted. Observation arrays, numeric
values, labels, detector outcomes, and rendered text never enter this bundle.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping

from .exp05_runner_v1 import (
    EvaluatedFormalV4ExplanationUnitV1,
    Exp05RunAuthorizationV1,
    FormalV4RuntimeMaterializationReceiptV1,
    validate_evaluated_formal_v4_explanation_unit_v1,
)
from .explanation_fidelity_v1 import (
    ExplanationFidelityCheckV1,
    FormalV4ExplanationFidelityResultV1,
    FormalV4ExplanationRecordV1,
    MaterializedFormalV4TraceV1,
)
from .formal_v4_authority_v1 import NumericReferenceBindingV1, canonical_document_hash_v1


EXP05_COHORT_CUSTODY_VERSION = "VALIDATION_V2_EXP05_COHORT_CUSTODY_V1"
_HEX = frozenset("0123456789abcdef")
_ZERO = "0" * 64


class Exp05CustodyError(ValueError):
    pass


def _fail(code: str) -> None:
    raise Exp05CustodyError(code)


def _sha(value: object, code: str) -> str:
    if type(value) is not str or len(value) != 64 or set(value) - _HEX:
        _fail(code)
    return value


def _text(value: object, code: str) -> str:
    if type(value) is not str or not value or value in (".", "..") or any(ch in value for ch in ("/", "\\", ":")):
        _fail(code)
    return value


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


@dataclass(frozen=True)
class Exp05OpportunityManifestEntryV1:
    opportunity_id: str
    relation_id: str

    def __post_init__(self) -> None:
        _text(self.opportunity_id, "EXP05_OPPORTUNITY_ID_INVALID")
        _text(self.relation_id, "EXP05_RELATION_ID_INVALID")

    def to_dict(self) -> dict[str, str]:
        return {"opportunity_id": self.opportunity_id, "relation_id": self.relation_id}


@dataclass(frozen=True)
class Exp05OpportunityManifestV1:
    entries: tuple[Exp05OpportunityManifestEntryV1, ...]
    manifest_hash: str = ""

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple or not self.entries or any(type(item) is not Exp05OpportunityManifestEntryV1 for item in self.entries):
            _fail("EXP05_OPPORTUNITY_MANIFEST_INVALID")
        keys = tuple((item.opportunity_id, item.relation_id) for item in self.entries)
        if keys != tuple(sorted(set(keys))):
            _fail("EXP05_OPPORTUNITY_MANIFEST_ORDER_OR_DUPLICATE")
        expected = canonical_document_hash_v1(self.payload())
        if self.manifest_hash and self.manifest_hash != expected:
            _fail("EXP05_OPPORTUNITY_MANIFEST_HASH_MISMATCH")

    def payload(self) -> dict[str, Any]:
        return {
            "entries": [item.to_dict() for item in self.entries],
            "entry_count": len(self.entries),
            "schema": "paperworks.validation_v2.exp05_opportunity_manifest_v1",
            "schema_version": "1.0.0",
        }


def build_exp05_opportunity_manifest_v1(
    entries: tuple[Exp05OpportunityManifestEntryV1, ...],
) -> Exp05OpportunityManifestV1:
    provisional = Exp05OpportunityManifestV1(entries=entries)
    return replace(provisional, manifest_hash=canonical_document_hash_v1(provisional.payload()))


@dataclass(frozen=True)
class Exp05EvaluatedUnitReferenceV1:
    opportunity_id: str
    relation_id: str
    outcome: str
    reason: str
    runtime_trace_hash: str
    materialized_trace_hash: str
    explanation_hash: str
    fidelity_result_hash: str
    materialization_receipt_hash: str
    full_unit_artifact_sha256: str
    full_unit_freeze_receipt_hash: str
    unit_hash: str

    def __post_init__(self) -> None:
        _text(self.opportunity_id, "EXP05_UNIT_OPPORTUNITY_ID_INVALID")
        _text(self.relation_id, "EXP05_UNIT_RELATION_ID_INVALID")
        _text(self.reason, "EXP05_UNIT_REASON_INVALID")
        if self.outcome not in ("PASS", "FAIL", "ABSTAIN"):
            _fail("EXP05_UNIT_OUTCOME_INVALID")
        for name in (
            "runtime_trace_hash", "materialized_trace_hash", "explanation_hash",
            "fidelity_result_hash", "materialization_receipt_hash", "unit_hash",
            "full_unit_artifact_sha256", "full_unit_freeze_receipt_hash",
        ):
            _sha(getattr(self, name), f"EXP05_{name.upper()}_INVALID")

    def to_dict(self) -> dict[str, str]:
        return {
            "explanation_hash": self.explanation_hash,
            "fidelity_result_hash": self.fidelity_result_hash,
            "materialization_receipt_hash": self.materialization_receipt_hash,
            "materialized_trace_hash": self.materialized_trace_hash,
            "full_unit_artifact_sha256": self.full_unit_artifact_sha256,
            "full_unit_freeze_receipt_hash": self.full_unit_freeze_receipt_hash,
            "opportunity_id": self.opportunity_id,
            "outcome": self.outcome,
            "reason": self.reason,
            "relation_id": self.relation_id,
            "runtime_trace_hash": self.runtime_trace_hash,
            "unit_hash": self.unit_hash,
        }


@dataclass(frozen=True)
class Exp05EvaluatedCohortBundleV1:
    cohort_id: str
    preregistration_hash: str
    opportunity_manifest_hash: str
    opportunity_count: int
    d1_native_outcome_binding_hash: str
    evaluated_units: tuple[Exp05EvaluatedUnitReferenceV1, ...]
    bundle_hash: str = ""

    def __post_init__(self) -> None:
        _text(self.cohort_id, "EXP05_COHORT_ID_INVALID")
        for value, code in (
            (self.preregistration_hash, "EXP05_PREREGISTRATION_HASH_INVALID"),
            (self.opportunity_manifest_hash, "EXP05_MANIFEST_HASH_INVALID"),
            (self.d1_native_outcome_binding_hash, "EXP05_D1_OUTCOME_BINDING_HASH_INVALID"),
        ):
            _sha(value, code)
        if type(self.opportunity_count) is not int or self.opportunity_count <= 0:
            _fail("EXP05_OPPORTUNITY_COUNT_INVALID")
        if type(self.evaluated_units) is not tuple or any(type(item) is not Exp05EvaluatedUnitReferenceV1 for item in self.evaluated_units):
            _fail("EXP05_EVALUATED_UNIT_REFERENCES_INVALID")
        keys = tuple((item.opportunity_id, item.relation_id) for item in self.evaluated_units)
        if keys != tuple(sorted(set(keys))) or len(keys) != self.opportunity_count:
            _fail("EXP05_COHORT_ORDER_COUNT_OR_DUPLICATE_INVALID")
        for field in (
            "runtime_trace_hash", "materialized_trace_hash", "explanation_hash",
            "fidelity_result_hash", "materialization_receipt_hash", "unit_hash",
        ):
            values = tuple(getattr(item, field) for item in self.evaluated_units)
            if len(set(values)) != len(values):
                _fail(f"EXP05_DUPLICATE_{field.upper()}")
        expected = canonical_document_hash_v1(self.payload())
        if self.bundle_hash and self.bundle_hash != expected:
            _fail("EXP05_COHORT_BUNDLE_HASH_MISMATCH")

    def payload(self) -> dict[str, Any]:
        strata: dict[str, int] = {}
        for item in self.evaluated_units:
            key = f"{item.outcome}:{item.reason}"
            strata[key] = strata.get(key, 0) + 1
        return {
            "cohort_id": self.cohort_id,
            "custody_version": EXP05_COHORT_CUSTODY_VERSION,
            "d1_native_outcome_binding_hash": self.d1_native_outcome_binding_hash,
            "evaluated_units": [item.to_dict() for item in self.evaluated_units],
            "labels_accessed": False,
            "llm_calls": 0,
            "opportunity_count": self.opportunity_count,
            "opportunity_manifest_hash": self.opportunity_manifest_hash,
            "outcome_reason_strata": dict(sorted(strata.items())),
            "preregistration_hash": self.preregistration_hash,
            "provider_calls": 0,
            "raw_numeric_values_embedded": False,
            "raw_observations_embedded": False,
            "schema": "paperworks.validation_v2.exp05_evaluated_cohort_bundle_v1",
            "schema_version": "1.0.0",
            "test2_accessed": False,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "bundle_hash": self.bundle_hash}


def build_exp05_evaluated_cohort_bundle_v1(
    *,
    cohort_id: str,
    preregistration_hash: str,
    opportunity_manifest: Exp05OpportunityManifestV1,
    d1_native_outcome_binding_hash: str,
    units: tuple[EvaluatedFormalV4ExplanationUnitV1, ...],
    full_unit_receipts: tuple[FullExp05UnitFreezeReceiptV1, ...],
) -> Exp05EvaluatedCohortBundleV1:
    if type(opportunity_manifest) is not Exp05OpportunityManifestV1:
        _fail("EXP05_OPPORTUNITY_MANIFEST_TYPE_INVALID")
    replayed_manifest = build_exp05_opportunity_manifest_v1(opportunity_manifest.entries)
    if replayed_manifest != opportunity_manifest:
        _fail("EXP05_OPPORTUNITY_MANIFEST_REPLAY_MISMATCH")
    if type(units) is not tuple or any(type(item) is not EvaluatedFormalV4ExplanationUnitV1 for item in units):
        _fail("EXP05_EVALUATED_UNITS_TYPE_INVALID")
    if (
        type(full_unit_receipts) is not tuple
        or len(full_unit_receipts) != len(units)
        or any(type(item) is not FullExp05UnitFreezeReceiptV1 for item in full_unit_receipts)
    ):
        _fail("EXP05_FULL_UNIT_RECEIPT_CENSUS_INVALID")
    references: list[Exp05EvaluatedUnitReferenceV1] = []
    for unit, full_receipt in zip(units, full_unit_receipts, strict=True):
        validate_evaluated_formal_v4_explanation_unit_v1(unit)
        if unit.materialization_receipt.preregistration_hash != preregistration_hash:
            _fail("EXP05_UNIT_PREREGISTRATION_MISMATCH")
        trace = unit.materialized_trace
        if (
            _PUBLISHED_FULL_UNITS.get(full_receipt.receipt_hash) != full_receipt
            or full_receipt.unit_hash != unit.unit_hash
            or full_receipt.opportunity_id != trace.opportunity_id
            or full_receipt.relation_id != trace.relation_id
        ):
            _fail("EXP05_FULL_UNIT_RECEIPT_NOT_PERSISTED_OR_MISMATCHED")
        references.append(Exp05EvaluatedUnitReferenceV1(
            opportunity_id=trace.opportunity_id,
            relation_id=trace.relation_id,
            outcome=trace.final_outcome,
            reason=trace.reason,
            runtime_trace_hash=unit.runtime_trace_hash,
            materialized_trace_hash=trace.self_hash,
            explanation_hash=unit.explanation.artifact_hash,
            fidelity_result_hash=unit.fidelity_result.result_hash,
            materialization_receipt_hash=unit.materialization_receipt.receipt_hash,
            full_unit_artifact_sha256=full_receipt.artifact_file_sha256,
            full_unit_freeze_receipt_hash=full_receipt.receipt_hash,
            unit_hash=unit.unit_hash,
        ))
    ordered = tuple(references)
    observed_keys = tuple((item.opportunity_id, item.relation_id) for item in ordered)
    expected_keys = tuple((item.opportunity_id, item.relation_id) for item in opportunity_manifest.entries)
    if observed_keys != expected_keys:
        _fail("EXP05_COHORT_INCOMPLETE_OR_ORPHANED")
    provisional = Exp05EvaluatedCohortBundleV1(
        cohort_id=cohort_id,
        preregistration_hash=preregistration_hash,
        opportunity_manifest_hash=opportunity_manifest.manifest_hash,
        opportunity_count=len(opportunity_manifest.entries),
        d1_native_outcome_binding_hash=d1_native_outcome_binding_hash,
        evaluated_units=ordered,
    )
    return replace(provisional, bundle_hash=canonical_document_hash_v1(provisional.payload()))


def _numeric_bindings_from_document(value: object) -> tuple[NumericReferenceBindingV1, ...]:
    if type(value) is not list:
        _fail("EXP05_FULL_UNIT_NUMERIC_BINDINGS_INVALID")
    try:
        return tuple(NumericReferenceBindingV1(**item) for item in value)
    except (TypeError, ValueError) as exc:
        raise Exp05CustodyError("EXP05_FULL_UNIT_NUMERIC_BINDINGS_INVALID") from exc


def _typed_fields(cls: type, document: Mapping[str, Any]) -> dict[str, Any]:
    return {item.name: document[item.name] for item in fields(cls)}


def _replay_full_unit_document(document: Mapping[str, Any]) -> EvaluatedFormalV4ExplanationUnitV1:
    required = {
        "explanation", "fidelity_result", "materialization_receipt", "materialized_trace",
        "run_authorization", "runtime_trace_hash", "schema", "schema_version", "unit_hash",
    }
    if type(document) is not dict or set(document) != required:
        _fail("EXP05_FULL_UNIT_DOCUMENT_SHAPE_INVALID")
    if (
        document["schema"] != "paperworks.validation_v2.exp05_full_evaluated_unit_v1"
        or document["schema_version"] != "1.0.0"
    ):
        _fail("EXP05_FULL_UNIT_SCHEMA_INVALID")
    try:
        authorization_document = document["run_authorization"]
        authorization = Exp05RunAuthorizationV1(**_typed_fields(Exp05RunAuthorizationV1, authorization_document))
        trace_document = document["materialized_trace"]
        trace_values = _typed_fields(MaterializedFormalV4TraceV1, trace_document)
        trace_values["ordered_numeric_reference_bindings"] = _numeric_bindings_from_document(
            trace_document["ordered_numeric_reference_bindings"]
        )
        trace = MaterializedFormalV4TraceV1(**trace_values)
        explanation_document = document["explanation"]
        explanation_values = _typed_fields(FormalV4ExplanationRecordV1, explanation_document)
        explanation_values["ordered_numeric_reference_bindings"] = _numeric_bindings_from_document(
            explanation_document["ordered_numeric_reference_bindings"]
        )
        explanation = FormalV4ExplanationRecordV1(**explanation_values)
        fidelity_document = document["fidelity_result"]
        fidelity_values = _typed_fields(FormalV4ExplanationFidelityResultV1, fidelity_document)
        fidelity_values["checks"] = tuple(
            ExplanationFidelityCheckV1(**item) for item in fidelity_document["checks"]
        )
        fidelity = FormalV4ExplanationFidelityResultV1(**fidelity_values)
        receipt_document = document["materialization_receipt"]
        receipt = FormalV4RuntimeMaterializationReceiptV1(**_typed_fields(
            FormalV4RuntimeMaterializationReceiptV1, receipt_document,
        ))
        unit = EvaluatedFormalV4ExplanationUnitV1(
            run_authorization=authorization,
            runtime_trace_hash=document["runtime_trace_hash"],
            materialized_trace=trace,
            explanation=explanation,
            fidelity_result=fidelity,
            materialization_receipt=receipt,
            unit_hash=document["unit_hash"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise Exp05CustodyError("EXP05_FULL_UNIT_TYPED_REPLAY_FAILED") from exc
    if (
        authorization.to_dict() != authorization_document
        or trace.to_dict() != trace_document
        or explanation.to_dict() != explanation_document
        or fidelity.to_dict() != fidelity_document
        or receipt.to_dict() != receipt_document
    ):
        _fail("EXP05_FULL_UNIT_NESTED_DOCUMENT_REPLAY_MISMATCH")
    validate_evaluated_formal_v4_explanation_unit_v1(unit)
    if _full_unit_document(unit) != document:
        _fail("EXP05_FULL_UNIT_DOCUMENT_REPLAY_MISMATCH")
    return unit


def _full_unit_document(unit: EvaluatedFormalV4ExplanationUnitV1) -> dict[str, Any]:
    validate_evaluated_formal_v4_explanation_unit_v1(unit)
    return {
        "explanation": unit.explanation.to_dict(),
        "fidelity_result": unit.fidelity_result.to_dict(),
        "materialization_receipt": unit.materialization_receipt.to_dict(),
        "materialized_trace": unit.materialized_trace.to_dict(),
        "run_authorization": unit.run_authorization.to_dict(),
        "runtime_trace_hash": unit.runtime_trace_hash,
        "schema": "paperworks.validation_v2.exp05_full_evaluated_unit_v1",
        "schema_version": "1.0.0",
        "unit_hash": unit.unit_hash,
    }


@dataclass(frozen=True)
class FullExp05UnitFreezeReceiptV1:
    opportunity_id: str
    relation_id: str
    unit_hash: str
    artifact_file_sha256: str
    byte_count: int
    publication_method: str
    file_fsync: bool
    directory_fsync: str
    reopened_bytes_match: bool
    receipt_hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "artifact_file_sha256": self.artifact_file_sha256,
            "byte_count": self.byte_count,
            "directory_fsync": self.directory_fsync,
            "file_fsync": self.file_fsync,
            "opportunity_id": self.opportunity_id,
            "publication_method": self.publication_method,
            "relation_id": self.relation_id,
            "reopened_bytes_match": self.reopened_bytes_match,
            "schema": "paperworks.validation_v2.exp05_full_unit_freeze_receipt_v1",
            "schema_version": "1.0.0",
            "state": "FULL_UNIT_FROZEN_REOPENED_REPLAYED",
            "unit_hash": self.unit_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "receipt_hash": self.receipt_hash}


_PUBLISHED_FULL_UNITS: dict[str, FullExp05UnitFreezeReceiptV1] = {}


def _validate_full_unit_receipt_document(document: Mapping[str, Any]) -> FullExp05UnitFreezeReceiptV1:
    expected = set(FullExp05UnitFreezeReceiptV1.__dataclass_fields__) | {"schema", "schema_version", "state"}
    if type(document) is not dict or set(document) != expected:
        _fail("EXP05_FULL_UNIT_RECEIPT_SHAPE_INVALID")
    if (
        document["schema"] != "paperworks.validation_v2.exp05_full_unit_freeze_receipt_v1"
        or document["schema_version"] != "1.0.0"
        or document["state"] != "FULL_UNIT_FROZEN_REOPENED_REPLAYED"
    ):
        _fail("EXP05_FULL_UNIT_RECEIPT_CONTRACT_INVALID")
    receipt = FullExp05UnitFreezeReceiptV1(**_typed_fields(FullExp05UnitFreezeReceiptV1, document))
    for value, code in (
        (receipt.unit_hash, "EXP05_FULL_UNIT_HASH_INVALID"),
        (receipt.artifact_file_sha256, "EXP05_FULL_UNIT_FILE_HASH_INVALID"),
        (receipt.receipt_hash, "EXP05_FULL_UNIT_RECEIPT_HASH_INVALID"),
    ):
        _sha(value, code)
    if (
        receipt.byte_count <= 0
        or receipt.publication_method != "NO_OVERWRITE_LINK_PUBLISH"
        or receipt.file_fsync is not True
        or receipt.directory_fsync not in ("PERFORMED", "UNSUPPORTED_WINDOWS")
        or receipt.reopened_bytes_match is not True
        or receipt.receipt_hash != canonical_document_hash_v1(receipt.payload())
    ):
        _fail("EXP05_FULL_UNIT_RECEIPT_REPLAY_MISMATCH")
    return receipt


def persist_exp05_full_evaluated_unit_v1(
    unit: EvaluatedFormalV4ExplanationUnitV1,
    *,
    artifact_path: Path,
    receipt_path: Path,
) -> FullExp05UnitFreezeReceiptV1:
    document = _full_unit_document(unit)
    content = _canonical_bytes(document)
    artifact_replay, directory_status = _publish_no_overwrite(artifact_path, content)
    provisional = FullExp05UnitFreezeReceiptV1(
        opportunity_id=unit.materialized_trace.opportunity_id,
        relation_id=unit.materialized_trace.relation_id,
        unit_hash=unit.unit_hash,
        artifact_file_sha256=sha256(content).hexdigest(),
        byte_count=len(content),
        publication_method="NO_OVERWRITE_LINK_PUBLISH",
        file_fsync=True,
        directory_fsync=directory_status,
        reopened_bytes_match=True,
    )
    receipt = replace(provisional, receipt_hash=canonical_document_hash_v1(provisional.payload()))
    receipt_replay, _ = _publish_no_overwrite(receipt_path, _canonical_bytes(receipt.to_dict()))
    _replay_exp05_full_evaluated_unit_bytes_v1(
        artifact_bytes=artifact_replay,
        receipt_bytes=receipt_replay,
        expected_receipt=receipt,
    )
    _PUBLISHED_FULL_UNITS[receipt.receipt_hash] = receipt
    return receipt


def _replay_exp05_full_evaluated_unit_bytes_v1(
    *,
    artifact_bytes: bytes,
    receipt_bytes: bytes,
    expected_receipt: FullExp05UnitFreezeReceiptV1,
) -> EvaluatedFormalV4ExplanationUnitV1:
    """Validate one already reopened durable unit without another file read."""

    try:
        document = json.loads(artifact_bytes.decode("utf-8"))
        receipt_document = json.loads(receipt_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        _fail("EXP05_FULL_UNIT_REPLAY_PARSE_FAILED")
    receipt = _validate_full_unit_receipt_document(receipt_document)
    unit = _replay_full_unit_document(document)
    if receipt != expected_receipt:
        _fail("EXP05_FULL_UNIT_EXPECTED_RECEIPT_MISMATCH")
    if (
        receipt.artifact_file_sha256 != sha256(artifact_bytes).hexdigest()
        or receipt.byte_count != len(artifact_bytes)
        or receipt.unit_hash != unit.unit_hash
        or receipt.opportunity_id != unit.materialized_trace.opportunity_id
        or receipt.relation_id != unit.materialized_trace.relation_id
    ):
        _fail("EXP05_FULL_UNIT_FROZEN_BINDING_MISMATCH")
    return unit


def replay_exp05_full_evaluated_unit_v1(
    *,
    artifact_path: Path,
    receipt_path: Path,
    expected_receipt: FullExp05UnitFreezeReceiptV1,
) -> EvaluatedFormalV4ExplanationUnitV1:
    if type(expected_receipt) is not FullExp05UnitFreezeReceiptV1:
        _fail("EXP05_FULL_UNIT_EXPECTED_RECEIPT_TYPE_INVALID")
    for path in (artifact_path, receipt_path):
        if not isinstance(path, Path) or not path.is_absolute() or not path.exists() or path.is_symlink():
            _fail("EXP05_FULL_UNIT_REPLAY_PATH_INVALID")
        if not stat.S_ISREG(path.lstat().st_mode):
            _fail("EXP05_FULL_UNIT_REPLAY_NONREGULAR_FILE")
    try:
        artifact_bytes = artifact_path.read_bytes()
        receipt_bytes = receipt_path.read_bytes()
    except OSError:
        _fail("EXP05_FULL_UNIT_REPLAY_PARSE_FAILED")
    unit = _replay_exp05_full_evaluated_unit_bytes_v1(
        artifact_bytes=artifact_bytes,
        receipt_bytes=receipt_bytes,
        expected_receipt=expected_receipt,
    )
    # A verified replay is the process-local proof consumed by cohort assembly.
    # Re-populating this index makes durable custody usable after a process
    # restart without weakening the no-path public cohort artifact.
    _PUBLISHED_FULL_UNITS[expected_receipt.receipt_hash] = expected_receipt
    return unit


@dataclass(frozen=True)
class HashOnlyExp05BundleFreezeReceiptV1:
    cohort_id: str
    bundle_hash: str
    bundle_file_sha256: str
    opportunity_manifest_hash: str
    d1_native_outcome_binding_hash: str
    unit_count: int
    byte_count: int
    publication_method: str
    file_fsync: bool
    directory_fsync: str
    reopened_bytes_match: bool
    receipt_hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "bundle_file_sha256": self.bundle_file_sha256,
            "bundle_hash": self.bundle_hash,
            "byte_count": self.byte_count,
            "cohort_id": self.cohort_id,
            "d1_native_outcome_binding_hash": self.d1_native_outcome_binding_hash,
            "directory_fsync": self.directory_fsync,
            "file_fsync": self.file_fsync,
            "opportunity_manifest_hash": self.opportunity_manifest_hash,
            "publication_method": self.publication_method,
            "reopened_bytes_match": self.reopened_bytes_match,
            "schema": "paperworks.validation_v2.exp05_bundle_freeze_receipt_v1",
            "schema_version": "1.0.0",
            "state": "FROZEN_REOPENED_REPLAYED",
            "unit_count": self.unit_count,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "receipt_hash": self.receipt_hash}


def _assert_safe_target(path: Path) -> Path:
    if not isinstance(path, Path) or not path.is_absolute() or not path.parent.exists():
        _fail("EXP05_FREEZE_PATH_INVALID")
    if path.parent.is_symlink() or getattr(path.parent, "is_junction", lambda: False)():
        _fail("EXP05_FREEZE_LINKED_PARENT_REJECTED")
    if path.exists() or path.is_symlink():
        _fail("EXP05_FREEZE_OVERWRITE_REJECTED")
    return path


def _directory_fsync(parent: Path) -> str:
    if os.name == "nt":
        return "UNSUPPORTED_WINDOWS"
    descriptor = os.open(parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return "PERFORMED"


def _publish_no_overwrite(path: Path, content: bytes) -> tuple[bytes, str]:
    _assert_safe_target(path)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        _fail("EXP05_FREEZE_STALE_TEMP_REJECTED")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        metadata = temporary.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            _fail("EXP05_FREEZE_TEMP_NONREGULAR_FILE")
        os.link(temporary, path, follow_symlinks=False)
        temporary.unlink()
        directory_status = _directory_fsync(path.parent)
        replay = path.read_bytes()
        if replay != content:
            _fail("EXP05_FREEZE_REOPEN_MISMATCH")
        return replay, directory_status
    except Exp05CustodyError:
        raise
    except FileExistsError:
        _fail("EXP05_FREEZE_NO_OVERWRITE_REJECTED")
    except OSError as error:
        _fail(f"EXP05_FREEZE_IO_{type(error).__name__.upper()}")
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()
    raise AssertionError("unreachable")


def _validate_bundle_document(document: Mapping[str, Any]) -> Exp05EvaluatedCohortBundleV1:
    required = {
        "bundle_hash", "cohort_id", "custody_version", "d1_native_outcome_binding_hash",
        "evaluated_units", "labels_accessed", "llm_calls", "opportunity_count",
        "opportunity_manifest_hash", "outcome_reason_strata", "preregistration_hash",
        "provider_calls", "raw_numeric_values_embedded", "raw_observations_embedded",
        "schema", "schema_version", "test2_accessed",
    }
    if type(document) is not dict or set(document) != required:
        _fail("EXP05_BUNDLE_DOCUMENT_SHAPE_INVALID")
    if any(document[name] is not False for name in (
        "labels_accessed", "raw_numeric_values_embedded", "raw_observations_embedded", "test2_accessed",
    )) or document["llm_calls"] != 0 or document["provider_calls"] != 0:
        _fail("EXP05_BUNDLE_SAFETY_BOUNDARY_VIOLATION")
    if document["custody_version"] != EXP05_COHORT_CUSTODY_VERSION:
        _fail("EXP05_BUNDLE_CUSTODY_VERSION_MISMATCH")
    references = tuple(Exp05EvaluatedUnitReferenceV1(**item) for item in document["evaluated_units"])
    bundle = Exp05EvaluatedCohortBundleV1(
        cohort_id=document["cohort_id"], preregistration_hash=document["preregistration_hash"],
        opportunity_manifest_hash=document["opportunity_manifest_hash"],
        opportunity_count=document["opportunity_count"],
        d1_native_outcome_binding_hash=document["d1_native_outcome_binding_hash"],
        evaluated_units=references, bundle_hash=document["bundle_hash"],
    )
    if bundle.to_dict() != document:
        _fail("EXP05_BUNDLE_DOCUMENT_REPLAY_MISMATCH")
    return bundle


def _validate_receipt_document(document: Mapping[str, Any]) -> HashOnlyExp05BundleFreezeReceiptV1:
    required = {
        "bundle_file_sha256", "bundle_hash", "byte_count", "cohort_id",
        "d1_native_outcome_binding_hash", "directory_fsync", "file_fsync",
        "opportunity_manifest_hash", "publication_method", "receipt_hash",
        "reopened_bytes_match", "schema", "schema_version", "state", "unit_count",
    }
    if type(document) is not dict or set(document) != required:
        _fail("EXP05_RECEIPT_DOCUMENT_SHAPE_INVALID")
    if (
        document["schema"] != "paperworks.validation_v2.exp05_bundle_freeze_receipt_v1"
        or document["schema_version"] != "1.0.0"
        or document["state"] != "FROZEN_REOPENED_REPLAYED"
    ):
        _fail("EXP05_RECEIPT_CONTRACT_MISMATCH")
    receipt = HashOnlyExp05BundleFreezeReceiptV1(**{
        key: document[key] for key in HashOnlyExp05BundleFreezeReceiptV1.__dataclass_fields__
    })
    if (
        receipt.file_fsync is not True or receipt.reopened_bytes_match is not True
        or receipt.publication_method != "NO_OVERWRITE_LINK_PUBLISH"
        or receipt.directory_fsync not in ("PERFORMED", "UNSUPPORTED_WINDOWS")
        or receipt.receipt_hash != canonical_document_hash_v1(receipt.payload())
    ):
        _fail("EXP05_RECEIPT_REPLAY_MISMATCH")
    return receipt


def persist_exp05_evaluated_bundle_v1(
    bundle: Exp05EvaluatedCohortBundleV1,
    *,
    bundle_path: Path,
    receipt_path: Path,
) -> HashOnlyExp05BundleFreezeReceiptV1:
    if type(bundle) is not Exp05EvaluatedCohortBundleV1:
        _fail("EXP05_BUNDLE_TYPE_INVALID")
    if canonical_document_hash_v1(bundle.payload()) != bundle.bundle_hash:
        _fail("EXP05_BUNDLE_HASH_MISMATCH")
    content = _canonical_bytes(bundle.to_dict())
    bundle_replay, directory_status = _publish_no_overwrite(bundle_path, content)
    provisional = HashOnlyExp05BundleFreezeReceiptV1(
        cohort_id=bundle.cohort_id,
        bundle_hash=bundle.bundle_hash,
        bundle_file_sha256=sha256(content).hexdigest(),
        opportunity_manifest_hash=bundle.opportunity_manifest_hash,
        d1_native_outcome_binding_hash=bundle.d1_native_outcome_binding_hash,
        unit_count=bundle.opportunity_count,
        byte_count=len(content),
        publication_method="NO_OVERWRITE_LINK_PUBLISH",
        file_fsync=True,
        directory_fsync=directory_status,
        reopened_bytes_match=True,
    )
    receipt = replace(provisional, receipt_hash=canonical_document_hash_v1(provisional.payload()))
    receipt_replay, _ = _publish_no_overwrite(receipt_path, _canonical_bytes(receipt.to_dict()))
    _replay_exp05_evaluated_bundle_bytes_v1(
        bundle_bytes=bundle_replay,
        receipt_bytes=receipt_replay,
        expected_receipt=receipt,
    )
    return receipt


def _replay_exp05_evaluated_bundle_bytes_v1(
    *,
    bundle_bytes: bytes,
    receipt_bytes: bytes,
    expected_receipt: HashOnlyExp05BundleFreezeReceiptV1,
) -> Exp05EvaluatedCohortBundleV1:
    """Validate one already reopened durable bundle without another file read."""

    try:
        receipt_document = json.loads(receipt_bytes.decode("utf-8"))
        bundle_document = json.loads(bundle_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        _fail("EXP05_REPLAY_PARSE_FAILED")
    receipt = _validate_receipt_document(receipt_document)
    bundle = _validate_bundle_document(bundle_document)
    if receipt != expected_receipt:
        _fail("EXP05_EXPECTED_RECEIPT_MISMATCH")
    if (
        receipt.bundle_file_sha256 != sha256(bundle_bytes).hexdigest()
        or receipt.byte_count != len(bundle_bytes)
        or receipt.bundle_hash != bundle.bundle_hash
        or receipt.cohort_id != bundle.cohort_id
        or receipt.opportunity_manifest_hash != bundle.opportunity_manifest_hash
        or receipt.d1_native_outcome_binding_hash != bundle.d1_native_outcome_binding_hash
        or receipt.unit_count != bundle.opportunity_count
    ):
        _fail("EXP05_FROZEN_BUNDLE_BINDING_MISMATCH")
    return bundle


def replay_exp05_evaluated_bundle_v1(
    *,
    bundle_path: Path,
    receipt_path: Path,
    expected_receipt: HashOnlyExp05BundleFreezeReceiptV1,
) -> Exp05EvaluatedCohortBundleV1:
    if type(expected_receipt) is not HashOnlyExp05BundleFreezeReceiptV1:
        _fail("EXP05_EXPECTED_RECEIPT_TYPE_INVALID")
    for path in (bundle_path, receipt_path):
        if not isinstance(path, Path) or not path.is_absolute() or not path.exists() or path.is_symlink():
            _fail("EXP05_REPLAY_PATH_INVALID")
        if not stat.S_ISREG(path.lstat().st_mode):
            _fail("EXP05_REPLAY_NONREGULAR_FILE")
    try:
        bundle_bytes = bundle_path.read_bytes()
        receipt_bytes = receipt_path.read_bytes()
    except OSError:
        _fail("EXP05_REPLAY_PARSE_FAILED")
    return _replay_exp05_evaluated_bundle_bytes_v1(
        bundle_bytes=bundle_bytes,
        receipt_bytes=receipt_bytes,
        expected_receipt=expected_receipt,
    )


__all__ = [
    "EXP05_COHORT_CUSTODY_VERSION", "Exp05CustodyError", "Exp05EvaluatedCohortBundleV1",
    "Exp05EvaluatedUnitReferenceV1", "Exp05OpportunityManifestEntryV1",
    "Exp05OpportunityManifestV1", "FullExp05UnitFreezeReceiptV1",
    "HashOnlyExp05BundleFreezeReceiptV1",
    "build_exp05_evaluated_cohort_bundle_v1", "build_exp05_opportunity_manifest_v1",
    "persist_exp05_evaluated_bundle_v1", "persist_exp05_full_evaluated_unit_v1",
    "replay_exp05_evaluated_bundle_v1", "replay_exp05_full_evaluated_unit_v1",
]
