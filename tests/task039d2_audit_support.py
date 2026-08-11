"""Clearly fake fixtures for TASK-039D2 independent audit preparation tests."""

from __future__ import annotations

from typing import Any, Mapping

from paperworks.profiling.task039d2_audit_accounting_v1 import (
    PRIVATE_CONFIRMATION_LEDGER_ARTIFACT_TYPE,
    PRIVATE_CONFIRMATION_RECORD_ARTIFACT_TYPE,
    ArmTop20ProvenanceV1,
)
from paperworks.profiling.task039d2_audit_reference_v1 import (
    CONFIRMATION_POLICY_HASH,
    AuditD1SourceParameterV1,
    AuditD1TargetParameterV1,
    AuditDirectionalInputV1,
    D2DirectionalInputSetV1,
    PARAMETER_CLASS,
    SyntheticAuditValueMapV1,
)
from paperworks.v6.common import V6_FOUNDATION_SCHEMA_VERSION, stable_hash_v1
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCE_ROLES,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
)


def fake_hash(label: str) -> str:
    return stable_hash_v1({"synthetic_audit_fixture": label})


def _source_record(
    source: str,
    *,
    ledger_hash: str,
    threshold: float = 0.5,
    tolerance: float = 0.1,
) -> AuditD1SourceParameterV1:
    content = {
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d1_source_parameter_record_v1",
        "source": source,
        "semantic_role": FROZEN_SOURCE_ROLES[source],
        "source_noise_scale": 0.1,
        "nontrivial_amplitude_count": 99,
        "source_step_threshold": threshold,
        "source_stability_tolerance": tolerance,
        "parameter_status": "supported",
        "parameter_class": PARAMETER_CLASS,
        "fit_file_bindings": [
            fake_hash("fake-train1-binding"),
            fake_hash("fake-train2-binding"),
        ],
    }
    return AuditD1SourceParameterV1(
        source=source,
        semantic_role=FROZEN_SOURCE_ROLES[source],
        source_noise_scale=0.1,
        nontrivial_amplitude_count=99,
        source_step_threshold=threshold,
        source_stability_tolerance=tolerance,
        parameter_status="supported",
        fit_file_bindings=tuple(content["fit_file_bindings"]),
        d1_record_hash=stable_hash_v1(content),
        d1_source_ledger_hash=ledger_hash,
    )


def _target_record(
    target: str, *, ledger_hash: str, scale: float = 1.0
) -> AuditD1TargetParameterV1:
    content = {
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d1_target_parameter_record_v1",
        "target": target,
        "target_noise_scale": scale,
        "parameter_class": PARAMETER_CLASS,
        "fit_file_bindings": [
            fake_hash("fake-train1-binding"),
            fake_hash("fake-train2-binding"),
        ],
    }
    return AuditD1TargetParameterV1(
        target=target,
        target_noise_scale=scale,
        fit_file_bindings=tuple(content["fit_file_bindings"]),
        d1_record_hash=stable_hash_v1(content),
        d1_target_ledger_hash=ledger_hash,
    )


def make_input_set() -> D2DirectionalInputSetV1:
    source_ledger_hash = fake_hash("fake-D1-source-ledger")
    target_ledger_hash = fake_hash("fake-D1-target-ledger")
    directional_ledger_hash = fake_hash("fake-D1-directional-ledger")
    source_records = tuple(
        _source_record(source, ledger_hash=source_ledger_hash)
        for source in FROZEN_SOURCES
    )
    target_records = tuple(
        _target_record(target, ledger_hash=target_ledger_hash)
        for target in FROZEN_TARGETS
    )
    source_by_name = {item.source: item for item in source_records}
    target_by_name = {item.target: item for item in target_records}
    pairs = tuple(
        (FROZEN_SOURCES[index % 12], FROZEN_TARGETS[index // 12])
        for index in range(25)
    )
    directions: list[AuditDirectionalInputV1] = []
    for index, (source, target) in enumerate(pairs):
        source_directions = ("step_up", "step_down") if index < 20 else ("step_up",)
        for source_direction in source_directions:
            directions.append(
                AuditDirectionalInputV1(
                    source=source,
                    source_step_direction=source_direction,
                    target=target,
                    target_response_direction=(
                        "increase" if (index + (source_direction == "step_down")) % 2 == 0 else "decrease"
                    ),
                    selected_horizon_seconds=(1, 5, 10, 30, 60)[index % 5],
                    d1_source_parameter_record_hash=source_by_name[source].d1_record_hash,
                    d1_target_parameter_record_hash=target_by_name[target].d1_record_hash,
                    d1_directional_record_hash=fake_hash(
                        f"fake-D1-direction-{source}-{target}-{source_direction}"
                    ),
                )
            )
    return D2DirectionalInputSetV1(
        directional_inputs=tuple(directions),
        source_parameters=source_records,
        target_parameters=target_records,
        d1_source_ledger_hash=source_ledger_hash,
        d1_target_ledger_hash=target_ledger_hash,
        d1_directional_ledger_hash=directional_ledger_hash,
    )


def _metrics_for_status(status: str) -> dict[str, Any]:
    if status == "calibration_confirmed":
        return {
            "usable_response_count": 5,
            "right_censored_count": 0,
            "source_direction_unchanged": True,
            "selected_consistency": 0.6,
            "opposite_consistency": 0.4,
            "robust_effect_ratio": 1.0,
        }
    if status == "calibration_conflict":
        return {
            "usable_response_count": 4,
            "right_censored_count": 1,
            "source_direction_unchanged": True,
            "selected_consistency": 0.75,
            "opposite_consistency": 0.25,
            "robust_effect_ratio": 2.0,
        }
    raise ValueError(status)


def make_confirmation_ledger(
    input_set: D2DirectionalInputSetV1,
    *,
    status_by_identity: Mapping[tuple[str, str, str], str] | None = None,
    metrics_by_identity: Mapping[tuple[str, str, str], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    statuses = status_by_identity or {}
    metrics = metrics_by_identity or {}
    records: list[dict[str, Any]] = []
    for relation in input_set.directional_inputs:
        identity = (relation.source, relation.target, relation.source_step_direction)
        status = statuses.get(identity, "calibration_conflict")
        values = {**_metrics_for_status(status), **metrics.get(identity, {})}
        confirmed = (
            values["usable_response_count"] >= 5
            and values["source_direction_unchanged"]
            and values["selected_consistency"] > values["opposite_consistency"]
            and values["selected_consistency"] >= 0.60
            and values["robust_effect_ratio"] >= 1.0
        )
        derived_status = (
            "calibration_confirmed" if confirmed else "calibration_conflict"
        )
        record = {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": PRIVATE_CONFIRMATION_RECORD_ARTIFACT_TYPE,
            "input_binding_hash": relation.binding_hash,
            "d1_source_parameter_record_hash": relation.d1_source_parameter_record_hash,
            "d1_target_parameter_record_hash": relation.d1_target_parameter_record_hash,
            "d1_directional_record_hash": relation.d1_directional_record_hash,
            "source": relation.source,
            "source_step_direction": relation.source_step_direction,
            "target": relation.target,
            "target_response_direction": relation.target_response_direction,
            "selected_horizon_seconds": relation.selected_horizon_seconds,
            **values,
            "fit_parameters_reused_without_retuning": True,
            "alternative_horizon_search_performed": False,
            "opposite_direction_search_performed": False,
            "lower_ranked_fallback_used": False,
            "status": derived_status,
        }
        record["artifact_hash"] = stable_hash_v1(record)
        records.append(record)
    ledger = {
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": PRIVATE_CONFIRMATION_LEDGER_ARTIFACT_TYPE,
        "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
        "input_set_binding_hash": input_set.binding_hash,
        "records": records,
        "real_hai_values_embedded": False,
        "d1_private_records_embedded": False,
        "method_provenance_embedded": False,
    }
    ledger["artifact_hash"] = stable_hash_v1(ledger)
    return ledger


def rehash_ledger(ledger: dict[str, Any], *, record_index: int | None = None) -> None:
    if record_index is not None:
        record = ledger["records"][record_index]
        record["artifact_hash"] = stable_hash_v1(
            {key: value for key, value in record.items() if key != "artifact_hash"}
        )
    ledger["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in ledger.items() if key != "artifact_hash"}
    )


def make_arm_provenance(
    input_set: D2DirectionalInputSetV1,
    *,
    arm: str,
    supported_pairs: set[tuple[str, str]],
) -> ArmTop20ProvenanceV1:
    all_supported = {
        (item.source, item.target) for item in input_set.directional_inputs
    }
    if not supported_pairs <= all_supported:
        raise ValueError("requested supported pair is absent")
    fillers = [
        (source, target)
        for source in FROZEN_SOURCES
        for target in FROZEN_TARGETS
        if (source, target) not in all_supported
        and (source, target) not in supported_pairs
    ]
    pairs = set(supported_pairs)
    pairs.update(fillers[: 20 - len(pairs)])
    return ArmTop20ProvenanceV1(arm=arm, pairs=frozenset(pairs))


def synthetic_value_map(
    *,
    source_values: Mapping[str, list[float]] | None = None,
    target_values: Mapping[str, list[float]] | None = None,
    length: int = 160,
) -> SyntheticAuditValueMapV1:
    values: dict[str, list[float]] = {
        name: [0.0] * length for name in (*FROZEN_SOURCES, *FROZEN_TARGETS)
    }
    for name, sequence in (source_values or {}).items():
        values[name] = sequence
    for name, sequence in (target_values or {}).items():
        values[name] = sequence
    return SyntheticAuditValueMapV1(
        fixture_id="synthetic_audit_independent_reference", values=values
    )


def one_relation(
    input_set: D2DirectionalInputSetV1,
    *,
    source_direction: str = "step_up",
    target_direction: str = "increase",
    horizon: int = 1,
) -> AuditDirectionalInputV1:
    source = FROZEN_SOURCES[0]
    target = FROZEN_TARGETS[0]
    source_record = input_set.source_parameters[0]
    target_record = input_set.target_parameters[0]
    return AuditDirectionalInputV1(
        source=source,
        source_step_direction=source_direction,
        target=target,
        target_response_direction=target_direction,
        selected_horizon_seconds=horizon,
        d1_source_parameter_record_hash=source_record.d1_record_hash,
        d1_target_parameter_record_hash=target_record.d1_record_hash,
        d1_directional_record_hash=fake_hash(
            f"single-{source_direction}-{target_direction}-{horizon}"
        ),
    )


def stepped_source(
    *,
    direction: str,
    event_indices: tuple[int, ...] = (10, 30, 50, 70, 90, 110),
    length: int = 160,
) -> list[float]:
    values = [0.0] * length
    level = 0.0
    increment = 2.0 if direction == "step_up" else -2.0
    cursor = 0
    for event_index in event_indices:
        for index in range(cursor, event_index):
            values[index] = level
        level += increment
        cursor = event_index
    for index in range(cursor, length):
        values[index] = level
    return values


def response_target(
    *,
    event_indices: tuple[int, ...] = (10, 30, 50, 70, 90, 110),
    horizon: int = 1,
    direction: str = "increase",
    magnitude: float = 2.0,
    length: int = 160,
) -> list[float]:
    values = [0.0] * length
    signed = magnitude if direction == "increase" else -magnitude
    for event_index in event_indices:
        for index in range(event_index + horizon, event_index + horizon + 3):
            values[index] = signed
    return values


__all__ = [
    "fake_hash",
    "make_arm_provenance",
    "make_confirmation_ledger",
    "make_input_set",
    "one_relation",
    "rehash_ledger",
    "response_target",
    "stepped_source",
    "synthetic_value_map",
]
