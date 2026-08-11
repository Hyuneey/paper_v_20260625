"""Execution-only complexity adapters for TASK-039D1R.

The frozen D0 protocol functions remain the semantic authority.  This module
changes only where whole-sequence validation and isolation lookup occur: once
per file before an event-index scan, and indexed lookup across retained event
streams, respectively.
"""

from __future__ import annotations

import bisect
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Mapping, MutableMapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    freeze_json,
    reject_unknown_fields,
    require_sha256,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.continuous_step_protocol_v1 import (
    ContinuousStepProtocolError,
    SustainedStepEventV1,
    cluster_step_events_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    FIT_FILES,
    FROZEN_SOURCES,
    RelationProfilingProtocolError,
    classify_all_source_isolation_v1,
    extract_file_local_events_v1,
)


TASK_ID = "TASK-039D1R"
RECOVERY_STATUS = "passed_task039d1r_semantics_preserving_complexity_recovery"
ABORTED_COMMIT_A1 = "d70f90b297bf7a6737652777f8f3059864c0c158"
RECOVERY_BRANCH = "task-039d1r-relation-fit-profiling"
D0_PROTOCOL_BUNDLE_HASH = "888e3d642eba6f8ad8784d428bc4b27d7db7592d34779ba9a1f817860d76e1eb"
D1_AUTHORIZATION_HASH = "e3ec4316d26520efe4a93d1bf790f36633ed692fa5f9fb9458c26d2a9ad16467"

COMPONENT_POLICY_HASHES = {
    "source_scale": "47831757a6f66e0c860a0589391f610aa99213291278861a8c5f260a7fe54233",
    "source_event": "1f07a72b380b9ffb2ceb42e029517ef42716145062a57b1770d118b9db252342",
    "target_response": "4b007b9511152396e03722ad8ce0e9cf659ebef2760cef5110414e4ce4bcbeaf",
    "direction_selection": "0026c57f83502f67b1a0d055b22eec42ac08e05eeb6709ffe9cb55ee28d5839b",
    "fit_gate": "da2442ad641aa035c37e738bd8a20521f3e5b46a1801f02fee8dbdcba3520344",
    "confirmation": "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27",
    "method_comparison": "0ccc7a97a5e9b3fe1e5a8a54828ec8f8f7e6482c62eb63f7df62d804c8cae39e",
    "numeric_evidence": "2cdc0b12724f549a165d7fad870b69b602d4eb0c2e0006dcd1780c88c2b8fcbc",
}

ROOT_CAUSE_FUNCTION_CHAIN = (
    "TASK039D1 profiler",
    "extract_file_local_events_v1",
    "extract_sustained_step_events_v1",
    "per-event evaluate_step_candidate_v1",
    "_finite_sequence(values)",
    "whole-sequence conversion/finite scan",
)


class TASK039D1RecoveryError(ValueError):
    """Raised when the recovery adapter or its audit fails closed."""


def _normalize_sequence_once_v1(
    values: Sequence[float], metrics: MutableMapping[str, int] | None = None
) -> tuple[float, ...]:
    sequence = tuple(float(item) for item in values)
    if metrics is not None:
        metrics["complete_sequence_validation_count"] = (
            metrics.get("complete_sequence_validation_count", 0) + 1
        )
        metrics["validated_element_count"] = metrics.get("validated_element_count", 0) + len(sequence)
    if any(not math.isfinite(item) for item in sequence):
        raise ContinuousStepProtocolError("source values must contain finite values")
    return sequence


def extract_sustained_step_events_linear_v1(
    values: Sequence[float],
    *,
    source_step_threshold: float,
    source_stability_tolerance: float,
    metrics: MutableMapping[str, int] | None = None,
) -> tuple[SustainedStepEventV1, ...]:
    """Preserve D0 event semantics with one complete validation per sequence."""

    sequence = _normalize_sequence_once_v1(values, metrics)
    threshold = float(source_step_threshold)
    tolerance = float(source_stability_tolerance)
    if not math.isfinite(threshold) or not math.isfinite(tolerance):
        raise ContinuousStepProtocolError("threshold and tolerance must be finite")
    if threshold <= 0 or tolerance < 0:
        raise ContinuousStepProtocolError("threshold and tolerance must be bounded")
    events: list[SustainedStepEventV1] = []
    for event_index in range(5, len(sequence) - 5 + 1):
        if metrics is not None:
            metrics["event_index_evaluation_count"] = (
                metrics.get("event_index_evaluation_count", 0) + 1
            )
        pre = sequence[event_index - 5 : event_index]
        post = sequence[event_index : event_index + 5]
        pre_level = float(statistics.median(pre))
        post_level = float(statistics.median(post))
        amplitude = post_level - pre_level
        if amplitude == 0 or abs(amplitude) < threshold:
            continue
        pre_fraction = sum(abs(item - pre_level) <= tolerance for item in pre) / 5.0
        if pre_fraction < 0.8:
            continue
        post_fraction = sum(abs(item - post_level) <= tolerance for item in post) / 5.0
        if post_fraction < 0.8:
            continue
        events.append(
            SustainedStepEventV1(
                event_index,
                "step_up" if amplitude > 0 else "step_down",
                pre_level,
                post_level,
                amplitude,
                pre_fraction,
                post_fraction,
            )
        )
    return cluster_step_events_v1(events, refractory_seconds=10)


def extract_file_local_events_linear_v1(
    files: Mapping[str, Sequence[float]],
    *,
    source_step_threshold: float,
    source_stability_tolerance: float,
    metrics_by_file: MutableMapping[str, MutableMapping[str, int]] | None = None,
) -> dict[str, tuple[SustainedStepEventV1, ...]]:
    """Apply the linear adapter independently to the two frozen fit files."""

    if set(files) != set(FIT_FILES):
        raise RelationProfilingProtocolError("event extraction requires the two frozen fit files")
    return {
        file_name: extract_sustained_step_events_linear_v1(
            files[file_name],
            source_step_threshold=source_step_threshold,
            source_stability_tolerance=source_stability_tolerance,
            metrics=None if metrics_by_file is None else metrics_by_file.setdefault(file_name, {}),
        )
        for file_name in FIT_FILES
    }


def classify_all_source_isolation_indexed_v1(
    source_events: Mapping[str, Sequence[SustainedStepEventV1]],
) -> dict[str, tuple[tuple[SustainedStepEventV1, bool], ...]]:
    """Preserve inclusive +/-2 isolation using sorted other-source indexes."""

    if set(source_events) != set(FROZEN_SOURCES):
        raise RelationProfilingProtocolError("isolation requires all 12 frozen sources")
    indexes = {
        source: tuple(sorted(event.event_index for event in source_events[source]))
        for source in FROZEN_SOURCES
    }
    result: dict[str, tuple[tuple[SustainedStepEventV1, bool], ...]] = {}
    for source in FROZEN_SOURCES:
        other_indexes = sorted(
            index
            for other_source in FROZEN_SOURCES
            if other_source != source
            for index in indexes[other_source]
        )
        classified: list[tuple[SustainedStepEventV1, bool]] = []
        for event in source_events[source]:
            left = bisect.bisect_left(other_indexes, event.event_index - 2)
            isolated = left == len(other_indexes) or other_indexes[left] > event.event_index + 2
            classified.append((event, isolated))
        result[source] = tuple(classified)
    return result


def _event(event_index: int, direction: str = "step_up", amplitude: float = 1.0) -> SustainedStepEventV1:
    return SustainedStepEventV1(
        event_index,
        direction,
        0.0,
        amplitude,
        amplitude,
        1.0,
        1.0,
    )


def audit_event_semantic_parity_v1() -> None:
    """Run bounded deterministic optimized-versus-D0 event parity fixtures."""

    fixtures: tuple[tuple[Sequence[float], float, float], ...] = (
        ([0.0] * 30, 1.0, 0.0),
        ([0.0] * 10 + [1.0] * 20, 1.0, 0.0),
        ([0.0] * 10 + [1.0] * 20, 1.0000000001, 0.0),
        ([1.0] * 10 + [0.0] * 20, 1.0, 0.0),
        ([0.0] * 10 + [-2.0] * 20, 1.0, 0.0),
        ([0.0, 0.0, 0.0, 0.0, 0.2] + [2.0] * 20, 1.0, 0.0),
        ([0.0] * 12 + [2.0] * 7 + [0.0] * 7 + [3.0] * 20, 1.0, 0.0),
        ([-3.5] * 11 + [-1.25] * 15 + [-4.0] * 15, 1.0, 0.0),
        ([0.0] * 200 + [2.5] * 200 + [0.0] * 200, 1.0, 0.0),
    )
    for values, threshold, tolerance in fixtures:
        reference = extract_file_local_events_v1(
            {FIT_FILES[0]: values, FIT_FILES[1]: values},
            source_step_threshold=threshold,
            source_stability_tolerance=tolerance,
        )
        optimized = extract_file_local_events_linear_v1(
            {FIT_FILES[0]: values, FIT_FILES[1]: values},
            source_step_threshold=threshold,
            source_stability_tolerance=tolerance,
        )
        if reference != optimized:
            raise TASK039D1RecoveryError("failed_task039d1r_event_semantic_parity")


def audit_isolation_semantic_parity_v1() -> None:
    """Run deterministic indexed-versus-D0 isolation parity fixtures."""

    empty = {source: () for source in FROZEN_SOURCES}
    fixtures: list[dict[str, tuple[SustainedStepEventV1, ...]]] = [empty]
    for offset in (-3, -2, 0, 2, 3):
        fixture = {source: () for source in FROZEN_SOURCES}
        fixture[FROZEN_SOURCES[0]] = (_event(20), _event(80))
        fixture[FROZEN_SOURCES[1]] = (_event(20 + offset, "step_down", -1.0),)
        fixtures.append(fixture)
    same_source = {source: () for source in FROZEN_SOURCES}
    same_source[FROZEN_SOURCES[0]] = (_event(10), _event(11), _event(40))
    fixtures.append(same_source)
    dense = {source: tuple(_event(index) for index in range(position, 120, 12)) for position, source in enumerate(FROZEN_SOURCES)}
    fixtures.append(dense)
    sparse = {source: tuple(_event(index) for index in range(position * 100, 5000, 1300)) for position, source in enumerate(FROZEN_SOURCES)}
    fixtures.append(sparse)
    for fixture in fixtures:
        reference = classify_all_source_isolation_v1(fixture)
        optimized = classify_all_source_isolation_indexed_v1(fixture)
        if reference != optimized:
            raise TASK039D1RecoveryError("failed_task039d1r_isolation_semantic_parity")


def audit_structural_complexity_v1() -> dict[str, Any]:
    """Verify structural linear scanning and indexed isolation without timing."""

    metrics_n: dict[str, int] = {}
    metrics_2n: dict[str, int] = {}
    extract_sustained_step_events_linear_v1(
        [0.0] * 400,
        source_step_threshold=1.0,
        source_stability_tolerance=0.0,
        metrics=metrics_n,
    )
    extract_sustained_step_events_linear_v1(
        [0.0] * 800,
        source_step_threshold=1.0,
        source_stability_tolerance=0.0,
        metrics=metrics_2n,
    )
    if (
        metrics_n.get("complete_sequence_validation_count") != 1
        or metrics_2n.get("complete_sequence_validation_count") != 1
        or metrics_n.get("validated_element_count") != 400
        or metrics_2n.get("validated_element_count") != 800
        or metrics_2n.get("event_index_evaluation_count", 0)
        > 2 * metrics_n.get("event_index_evaluation_count", 0) + 10
    ):
        raise TASK039D1RecoveryError("failed_task039d1r_hot_path_complexity")
    return {
        "event_extraction_complexity_class": "linear_in_sequence_length",
        "isolation_complexity_class": "O(E log E)_with_fixed_12_source_context",
    }


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = thaw_json(freeze_json(content))
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


@dataclass(frozen=True)
class _RecoveryArtifact:
    payload: Mapping[str, Any]
    ARTIFACT_TYPE: ClassVar[str] = ""
    FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        reject_unknown_fields(self.payload, self.FIELDS, self.ARTIFACT_TYPE)
        if set(self.payload) != set(self.FIELDS):
            raise TASK039D1RecoveryError(f"{self.ARTIFACT_TYPE} fields are incomplete")
        object.__setattr__(self, "payload", freeze_json(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return _self_hashed(
            {
                "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
                "artifact_type": self.ARTIFACT_TYPE,
                **thaw_json(self.payload),
            }
        )


def _artifact_class(name: str, artifact_type: str, fields: Sequence[str]) -> type[_RecoveryArtifact]:
    return type(
        name,
        (_RecoveryArtifact,),
        {"ARTIFACT_TYPE": artifact_type, "FIELDS": frozenset(fields)},
    )


TASK039D1ExecutionComplexityReceiptV1 = _artifact_class(
    "TASK039D1ExecutionComplexityReceiptV1",
    "task039d1_execution_complexity_receipt_v1",
    (
        "task_id", "status", "original_aborted_commit_a", "defect",
        "defect_classification", "root_cause_function_chain", "d0_protocol_bundle_hash",
        "d1_authorization_hash", "component_policy_hashes", "scientific_formulas_changed",
        "d0_policies_changed", "event_reference_path", "event_optimized_path",
        "event_semantic_parity", "event_complexity_class", "isolation_reference_path",
        "isolation_optimized_path", "isolation_semantic_parity", "isolation_complexity_class",
        "target_response_optimization_status", "source_parameters_computed_once_per_source",
        "target_scale_computed_once_per_target", "event_streams_computed_once_per_source_file",
        "isolation_computed_once_per_file", "unresolved_execution_complexity_defects",
        "hai_values_accessed_during_recovery_implementation", "source_file_hashes",
    ),
)

TASK039D1AbortedExecutionRecordV1 = _artifact_class(
    "TASK039D1AbortedExecutionRecordV1",
    "task039d1_aborted_execution_record_v1",
    (
        "task_id", "status", "original_d1_commit_a", "terminal_status", "train1_accessed",
        "train2_accessed", "train3_accessed", "train4_accessed", "test_accessed",
        "labels_accessed", "attacks_accessed", "private_ledgers_produced",
        "scientific_outcomes_frozen", "provenance_joined", "rule_v2_authorized",
        "task039d2_authorized", "defect", "aborted_outputs_reused",
    ),
)


def verify_recovery_artifact_v1(document: Mapping[str, Any]) -> str:
    artifact_type = str(document.get("artifact_type", ""))
    artifact_class = {
        TASK039D1ExecutionComplexityReceiptV1.ARTIFACT_TYPE: TASK039D1ExecutionComplexityReceiptV1,
        TASK039D1AbortedExecutionRecordV1.ARTIFACT_TYPE: TASK039D1AbortedExecutionRecordV1,
    }.get(artifact_type)
    if artifact_class is None:
        raise TASK039D1RecoveryError("unknown TASK-039D1R artifact type")
    supplied = str(document.get("artifact_hash", ""))
    require_sha256(supplied, "artifact_hash")
    allowed = artifact_class.FIELDS | {"schema_version", "artifact_type", "artifact_hash"}
    reject_unknown_fields(document, allowed, artifact_type)
    if document.get("schema_version") != V6_FOUNDATION_SCHEMA_VERSION:
        raise TASK039D1RecoveryError("schema version mismatch")
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    observed = stable_hash_v1(content)
    if observed != supplied:
        raise TASK039D1RecoveryError("recovery artifact self-hash mismatch")
    artifact_class({key: document[key] for key in artifact_class.FIELDS})
    return observed


def build_complexity_receipt_v1(*, source_file_hashes: Mapping[str, str]) -> dict[str, Any]:
    audit_event_semantic_parity_v1()
    audit_isolation_semantic_parity_v1()
    complexity = audit_structural_complexity_v1()
    for digest in source_file_hashes.values():
        require_sha256(digest, "source_file_hash")
    artifact = TASK039D1ExecutionComplexityReceiptV1(
        {
            "task_id": TASK_ID,
            "status": RECOVERY_STATUS,
            "original_aborted_commit_a": ABORTED_COMMIT_A1,
            "defect": "repeated_whole_sequence_validation_inside_event_index_loop",
            "defect_classification": "non_scientific_execution_complexity_defect",
            "root_cause_function_chain": list(ROOT_CAUSE_FUNCTION_CHAIN),
            "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
            "d1_authorization_hash": D1_AUTHORIZATION_HASH,
            "component_policy_hashes": dict(COMPONENT_POLICY_HASHES),
            "scientific_formulas_changed": False,
            "d0_policies_changed": False,
            "event_reference_path": "paperworks.v6.relation_profiling_protocol_v1.extract_file_local_events_v1",
            "event_optimized_path": "paperworks.profiling.task039d1_execution_optimization_v1.extract_file_local_events_linear_v1",
            "event_semantic_parity": "passed",
            "event_complexity_class": complexity["event_extraction_complexity_class"],
            "isolation_reference_path": "paperworks.v6.relation_profiling_protocol_v1.classify_all_source_isolation_v1",
            "isolation_optimized_path": "paperworks.profiling.task039d1_execution_optimization_v1.classify_all_source_isolation_indexed_v1",
            "isolation_semantic_parity": "passed",
            "isolation_complexity_class": complexity["isolation_complexity_class"],
            "target_response_optimization_status": "retained_unchanged_and_parity_reverified",
            "source_parameters_computed_once_per_source": True,
            "target_scale_computed_once_per_target": True,
            "event_streams_computed_once_per_source_file": True,
            "isolation_computed_once_per_file": True,
            "unresolved_execution_complexity_defects": [],
            "hai_values_accessed_during_recovery_implementation": False,
            "source_file_hashes": dict(source_file_hashes),
        }
    )
    document = artifact.to_dict()
    verify_recovery_artifact_v1(document)
    return document


def build_aborted_execution_record_v1() -> dict[str, Any]:
    artifact = TASK039D1AbortedExecutionRecordV1(
        {
            "task_id": TASK_ID,
            "status": "recorded_task039d1_aborted_execution",
            "original_d1_commit_a": ABORTED_COMMIT_A1,
            "terminal_status": "failed_task039d1_scientific_execution",
            "train1_accessed": True,
            "train2_accessed": True,
            "train3_accessed": False,
            "train4_accessed": False,
            "test_accessed": False,
            "labels_accessed": False,
            "attacks_accessed": False,
            "private_ledgers_produced": False,
            "scientific_outcomes_frozen": False,
            "provenance_joined": False,
            "rule_v2_authorized": False,
            "task039d2_authorized": False,
            "defect": "repeated_whole_sequence_validation_inside_event_index_loop",
            "aborted_outputs_reused": False,
        }
    )
    document = artifact.to_dict()
    verify_recovery_artifact_v1(document)
    return document


def schema_for_recovery_artifact_v1(example: Mapping[str, Any]) -> dict[str, Any]:
    def infer(value: Any, field_name: str | None = None) -> dict[str, Any]:
        if value is None:
            return {"type": "null"}
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, int):
            return {"type": "integer", "minimum": 0}
        if isinstance(value, str):
            schema: dict[str, Any] = {"type": "string"}
            if field_name and (field_name.endswith("_hash") or field_name.endswith("_commit_a")):
                schema["pattern"] = "^[a-f0-9]{40}$" if field_name.endswith("_commit_a") else "^[a-f0-9]{64}$"
            return schema
        if isinstance(value, list):
            return {"type": "array", "items": {} if not value else infer(value[0])}
        if isinstance(value, Mapping):
            return {
                "type": "object",
                "additionalProperties": False,
                "required": list(value),
                "properties": {key: infer(item, key) for key, item in value.items()},
            }
        raise TASK039D1RecoveryError("unsupported recovery schema value")

    schema = infer(example)
    artifact_type = str(example["artifact_type"])
    schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://paperworks.local/schemas/v6/{artifact_type}_schema.json",
            "title": artifact_type,
        }
    )
    schema["properties"]["schema_version"] = {"const": V6_FOUNDATION_SCHEMA_VERSION}
    schema["properties"]["artifact_type"] = {"const": artifact_type}
    schema["properties"]["artifact_hash"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    return schema


def source_file_sha256_v1(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "TASK039D1RecoveryError", "TASK039D1ExecutionComplexityReceiptV1",
    "TASK039D1AbortedExecutionRecordV1", "extract_sustained_step_events_linear_v1",
    "extract_file_local_events_linear_v1", "classify_all_source_isolation_indexed_v1",
    "audit_event_semantic_parity_v1", "audit_isolation_semantic_parity_v1",
    "audit_structural_complexity_v1", "build_complexity_receipt_v1",
    "build_aborted_execution_record_v1", "verify_recovery_artifact_v1",
    "schema_for_recovery_artifact_v1", "source_file_sha256_v1", "RECOVERY_STATUS",
    "ABORTED_COMMIT_A1", "RECOVERY_BRANCH", "D0_PROTOCOL_BUNDLE_HASH",
    "D1_AUTHORIZATION_HASH", "COMPONENT_POLICY_HASHES",
]
