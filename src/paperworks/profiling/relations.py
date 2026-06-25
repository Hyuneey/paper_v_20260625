"""High-resolution trigger-response profiling for supported relation pairs."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from paperworks.data import DataViewManifest, DataViewName, SplitManifest, assert_split_permitted
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.metadata import MetadataRegistry, ValueType, VariableRole


class RelationProfilingError(ValueError):
    """Raised when profiling or calibration inputs violate the project contract."""


@dataclass(frozen=True)
class RelationProfilingConfig:
    """Explicit policy for the initial binary-actuator to continuous-sensor profile."""

    max_response_delay_samples: int
    min_matched_response_count: int
    trigger_from: float = 0.0
    trigger_to: float = 1.0
    response_delta_floor: float = 0.0
    delay_quantile: float = 1.0
    magnitude_quantile: float = 0.0
    irregular_sampling_policy: str = "reject"
    timestamp_tolerance_seconds: float = 1e-6
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.max_response_delay_samples < 0:
            raise RelationProfilingError("max_response_delay_samples must be non-negative")
        if self.min_matched_response_count <= 0:
            raise RelationProfilingError("min_matched_response_count must be positive")
        if self.delay_quantile < 0.0 or self.delay_quantile > 1.0:
            raise RelationProfilingError("delay_quantile must be in [0, 1]")
        if self.magnitude_quantile < 0.0 or self.magnitude_quantile > 1.0:
            raise RelationProfilingError("magnitude_quantile must be in [0, 1]")
        if self.response_delta_floor < 0.0:
            raise RelationProfilingError("response_delta_floor must be non-negative")
        if self.irregular_sampling_policy != "reject":
            raise RelationProfilingError("only irregular_sampling_policy='reject' is currently supported")
        if self.timestamp_tolerance_seconds < 0.0:
            raise RelationProfilingError("timestamp_tolerance_seconds must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RelationProfilingConfig":
        return cls(
            max_response_delay_samples=int(data["max_response_delay_samples"]),
            min_matched_response_count=int(data["min_matched_response_count"]),
            trigger_from=float(data.get("trigger_from", 0.0)),
            trigger_to=float(data.get("trigger_to", 1.0)),
            response_delta_floor=float(data.get("response_delta_floor", 0.0)),
            delay_quantile=float(data.get("delay_quantile", 1.0)),
            magnitude_quantile=float(data.get("magnitude_quantile", 0.0)),
            irregular_sampling_policy=str(data.get("irregular_sampling_policy", "reject")),
            timestamp_tolerance_seconds=float(data.get("timestamp_tolerance_seconds", 1e-6)),
            config_version=str(data.get("config_version", "1.0")),
        )


@dataclass(frozen=True)
class TriggerEvent:
    source: str
    target: str
    trigger_index: int
    trigger_timestamp_seconds: float
    previous_state: float
    new_state: float
    status: str
    response_index: int | None = None
    response_delay_seconds: float | None = None
    response_magnitude: float | None = None

    def __post_init__(self) -> None:
        if self.trigger_index < 0:
            raise RelationProfilingError("trigger_index must be non-negative")
        if self.response_index is not None and self.response_index < self.trigger_index:
            raise RelationProfilingError("response_index cannot precede trigger_index")
        if self.status not in {"matched", "missing_response", "right_censored"}:
            raise RelationProfilingError(f"unsupported trigger status: {self.status}")
        if self.status == "matched":
            if self.response_index is None or self.response_delay_seconds is None or self.response_magnitude is None:
                raise RelationProfilingError("matched triggers require response fields")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TriggerEvent":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            trigger_index=int(data["trigger_index"]),
            trigger_timestamp_seconds=float(data["trigger_timestamp_seconds"]),
            previous_state=float(data["previous_state"]),
            new_state=float(data["new_state"]),
            status=str(data["status"]),
            response_index=int(data["response_index"]) if data.get("response_index") is not None else None,
            response_delay_seconds=(
                float(data["response_delay_seconds"]) if data.get("response_delay_seconds") is not None else None
            ),
            response_magnitude=float(data["response_magnitude"]) if data.get("response_magnitude") is not None else None,
        )


@dataclass(frozen=True)
class ResponseEvent:
    source: str
    target: str
    trigger_index: int
    response_index: int
    trigger_timestamp_seconds: float
    response_timestamp_seconds: float
    delay_seconds: float
    magnitude: float

    def __post_init__(self) -> None:
        if self.response_index < self.trigger_index:
            raise RelationProfilingError("response_index cannot precede trigger_index")
        if self.delay_seconds < 0.0:
            raise RelationProfilingError("delay_seconds must be non-negative")
        if self.magnitude <= 0.0:
            raise RelationProfilingError("response magnitude must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ResponseEvent":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            trigger_index=int(data["trigger_index"]),
            response_index=int(data["response_index"]),
            trigger_timestamp_seconds=float(data["trigger_timestamp_seconds"]),
            response_timestamp_seconds=float(data["response_timestamp_seconds"]),
            delay_seconds=float(data["delay_seconds"]),
            magnitude=float(data["magnitude"]),
        )


@dataclass(frozen=True)
class RelationProfile:
    source: str
    target: str
    relation_type: str
    source_view: str
    sampling_period_seconds: float
    trigger_count: int
    matched_response_count: int
    censored_or_missing_count: int
    delay_summary_seconds: Mapping[str, float]
    magnitude_summary: Mapping[str, float]
    normal_support_status: str
    upstream_artifact_ids: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "relation_profile"
    dataset: str = "SWaT"
    split_name: str = "calibration_normal"
    data_fingerprint: str = ""
    config_hash: str = ""
    code_commit: str | None = None
    random_seed: int | None = None
    created_at: str = "unspecified"
    trigger_events: tuple[TriggerEvent, ...] = field(default_factory=tuple)
    response_events: tuple[ResponseEvent, ...] = field(default_factory=tuple)
    missing_response_count: int = 0
    right_censored_count: int = 0
    overlapping_window_count: int = 0

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise RelationProfilingError(f"unsupported schema_version: {self.schema_version}")
        if self.artifact_type != "relation_profile":
            raise RelationProfilingError("artifact_type must be relation_profile")
        if self.relation_type != "binary_actuator_to_continuous_sensor":
            raise RelationProfilingError("unsupported relation_type")
        if self.source_view != "canonical_rule_view":
            raise RelationProfilingError("relation profiles must use canonical_rule_view")
        if self.sampling_period_seconds <= 0.0:
            raise RelationProfilingError("sampling_period_seconds must be positive")
        if self.trigger_count < 0 or self.matched_response_count < 0 or self.censored_or_missing_count < 0:
            raise RelationProfilingError("support counts must be non-negative")
        if self.trigger_count != len(self.trigger_events):
            raise RelationProfilingError("trigger_count must match trigger_events")
        if self.matched_response_count != len(self.response_events):
            raise RelationProfilingError("matched_response_count must match response_events")
        if self.censored_or_missing_count != self.missing_response_count + self.right_censored_count:
            raise RelationProfilingError("censored_or_missing_count mismatch")
        if self.normal_support_status not in {"supported", "INSUFFICIENT_NORMAL_SUPPORT"}:
            raise RelationProfilingError(f"unsupported normal_support_status: {self.normal_support_status}")
        if self.config_hash and len(self.config_hash) != 64:
            raise RelationProfilingError("config_hash must be empty or a 64-character hash")

    @property
    def profile_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "dataset": self.dataset,
            "split_name": self.split_name,
            "data_fingerprint": self.data_fingerprint,
            "config_hash": self.config_hash,
            "code_commit": self.code_commit,
            "random_seed": self.random_seed,
            "created_at": self.created_at,
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "source_view": self.source_view,
            "sampling_period_seconds": self.sampling_period_seconds,
            "trigger_count": self.trigger_count,
            "matched_response_count": self.matched_response_count,
            "censored_or_missing_count": self.censored_or_missing_count,
            "missing_response_count": self.missing_response_count,
            "right_censored_count": self.right_censored_count,
            "overlapping_window_count": self.overlapping_window_count,
            "delay_summary_seconds": dict(self.delay_summary_seconds),
            "magnitude_summary": dict(self.magnitude_summary),
            "normal_support_status": self.normal_support_status,
            "upstream_artifact_ids": list(self.upstream_artifact_ids),
            "trigger_events": [event.to_dict() for event in self.trigger_events],
            "response_events": [event.to_dict() for event in self.response_events],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RelationProfile":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            relation_type=str(data["relation_type"]),
            source_view=str(data["source_view"]),
            sampling_period_seconds=float(data["sampling_period_seconds"]),
            trigger_count=int(data["trigger_count"]),
            matched_response_count=int(data["matched_response_count"]),
            censored_or_missing_count=int(data["censored_or_missing_count"]),
            delay_summary_seconds={str(key): float(value) for key, value in data["delay_summary_seconds"].items()},
            magnitude_summary={str(key): float(value) for key, value in data["magnitude_summary"].items()},
            normal_support_status=str(data["normal_support_status"]),
            upstream_artifact_ids=tuple(str(item) for item in data.get("upstream_artifact_ids", ())),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "relation_profile")),
            dataset=str(data.get("dataset", "SWaT")),
            split_name=str(data.get("split_name", "calibration_normal")),
            data_fingerprint=str(data.get("data_fingerprint", "")),
            config_hash=str(data.get("config_hash", "")),
            code_commit=data.get("code_commit"),
            random_seed=data.get("random_seed"),
            created_at=str(data.get("created_at", "unspecified")),
            trigger_events=tuple(TriggerEvent.from_dict(item) for item in data.get("trigger_events", ())),
            response_events=tuple(ResponseEvent.from_dict(item) for item in data.get("response_events", ())),
            missing_response_count=int(data.get("missing_response_count", 0)),
            right_censored_count=int(data.get("right_censored_count", 0)),
            overlapping_window_count=int(data.get("overlapping_window_count", 0)),
        )


@dataclass(frozen=True)
class CalibrationRecord:
    parameter_name: str
    value: float
    unit: str
    method: str
    quantile_or_config: Mapping[str, Any]
    normal_support_count: int
    relation_profile_id: str
    calibration_split_id: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "calibration_record"

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise RelationProfilingError(f"unsupported schema_version: {self.schema_version}")
        if self.artifact_type != "calibration_record":
            raise RelationProfilingError("artifact_type must be calibration_record")
        if not self.parameter_name:
            raise RelationProfilingError("parameter_name is required")
        if len(self.relation_profile_id) != 64 or len(self.calibration_split_id) != 64:
            raise RelationProfilingError("profile and split ids must be 64-character hashes")
        if self.normal_support_count <= 0:
            raise RelationProfilingError("normal_support_count must be positive")
        if not math.isfinite(self.value):
            raise RelationProfilingError("calibration value must be finite")

    @property
    def calibration_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "parameter_name": self.parameter_name,
            "value": self.value,
            "unit": self.unit,
            "method": self.method,
            "quantile_or_config": dict(self.quantile_or_config),
            "normal_support_count": self.normal_support_count,
            "relation_profile_id": self.relation_profile_id,
            "calibration_split_id": self.calibration_split_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CalibrationRecord":
        return cls(
            parameter_name=str(data["parameter_name"]),
            value=float(data["value"]),
            unit=str(data["unit"]),
            method=str(data["method"]),
            quantile_or_config=dict(data["quantile_or_config"]),
            normal_support_count=int(data["normal_support_count"]),
            relation_profile_id=str(data["relation_profile_id"]),
            calibration_split_id=str(data["calibration_split_id"]),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "calibration_record")),
        )


@dataclass(frozen=True)
class RelationEvidencePack:
    source: str
    target: str
    relation_type: str
    recommended_rule_family: str
    relation_profile_id: str
    calibration_record_ids: Mapping[str, str]
    calibrated_parameters: Mapping[str, float]
    support_counts: Mapping[str, int]
    source_view: str
    sampling_period_seconds: float
    upstream_artifact_ids: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "relation_evidence_pack"

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise RelationProfilingError(f"unsupported schema_version: {self.schema_version}")
        if self.artifact_type != "relation_evidence_pack":
            raise RelationProfilingError("artifact_type must be relation_evidence_pack")
        if len(self.relation_profile_id) != 64:
            raise RelationProfilingError("relation_profile_id must be a 64-character hash")
        for parameter, calibration_id in self.calibration_record_ids.items():
            if parameter not in self.calibrated_parameters:
                raise RelationProfilingError(f"calibrated parameter missing value: {parameter}")
            if len(calibration_id) != 64:
                raise RelationProfilingError("calibration record ids must be 64-character hashes")
        if self.source_view != "canonical_rule_view":
            raise RelationProfilingError("evidence packs must use canonical_rule_view")
        if self.sampling_period_seconds <= 0.0:
            raise RelationProfilingError("sampling_period_seconds must be positive")

    @property
    def evidence_pack_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "recommended_rule_family": self.recommended_rule_family,
            "relation_profile_id": self.relation_profile_id,
            "calibration_record_ids": dict(self.calibration_record_ids),
            "calibrated_parameters": dict(self.calibrated_parameters),
            "support_counts": dict(self.support_counts),
            "source_view": self.source_view,
            "sampling_period_seconds": self.sampling_period_seconds,
            "upstream_artifact_ids": list(self.upstream_artifact_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RelationEvidencePack":
        return cls(
            source=str(data["source"]),
            target=str(data["target"]),
            relation_type=str(data["relation_type"]),
            recommended_rule_family=str(data["recommended_rule_family"]),
            relation_profile_id=str(data["relation_profile_id"]),
            calibration_record_ids={str(key): str(value) for key, value in data["calibration_record_ids"].items()},
            calibrated_parameters={str(key): float(value) for key, value in data["calibrated_parameters"].items()},
            support_counts={str(key): int(value) for key, value in data["support_counts"].items()},
            source_view=str(data["source_view"]),
            sampling_period_seconds=float(data["sampling_period_seconds"]),
            upstream_artifact_ids=tuple(str(item) for item in data.get("upstream_artifact_ids", ())),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            artifact_type=str(data.get("artifact_type", "relation_evidence_pack")),
        )


def profile_binary_actuator_to_continuous_sensor(
    *,
    source: str,
    target: str,
    series: Mapping[str, Sequence[float]],
    metadata: MetadataRegistry,
    split: SplitManifest,
    data_view: DataViewManifest,
    config: RelationProfilingConfig,
    timestamps_seconds: Sequence[float] | None = None,
    upstream_artifact_ids: Sequence[str] = (),
    dataset: str = "SWaT",
    data_fingerprint: str = "",
    code_commit: str | None = None,
    random_seed: int | None = None,
    created_at: str = "unspecified",
) -> RelationProfile:
    """Profile a supported pair on calibration_normal canonical-rule-view data."""

    assert_split_permitted(split.role, "profile_relation")
    _validate_canonical_rule_view(data_view)
    _validate_supported_metadata(source=source, target=target, metadata=metadata)
    source_values, target_values = _aligned_pair_series(series, source, target)
    timestamps = _timestamps(
        length=len(source_values),
        sampling_period_seconds=data_view.sampling_period_seconds,
        timestamps_seconds=timestamps_seconds,
        config=config,
    )

    triggers: list[TriggerEvent] = []
    responses: list[ResponseEvent] = []
    trigger_indexes = _trigger_indexes(
        values=source_values,
        trigger_from=config.trigger_from,
        trigger_to=config.trigger_to,
    )
    overlapping_window_count = sum(
        1
        for left, right in zip(trigger_indexes, trigger_indexes[1:])
        if right <= left + config.max_response_delay_samples
    )

    missing_response_count = 0
    right_censored_count = 0
    for trigger_index in trigger_indexes:
        baseline_index = trigger_index - 1
        baseline = target_values[baseline_index]
        max_index = trigger_index + config.max_response_delay_samples
        search_end = min(max_index, len(target_values) - 1)
        response_index: int | None = None
        magnitude: float | None = None

        for candidate_index in range(trigger_index, search_end + 1):
            delta = target_values[candidate_index] - baseline
            if delta > 0.0 and delta >= config.response_delta_floor:
                response_index = candidate_index
                magnitude = delta
                break

        if response_index is None:
            status = "right_censored" if max_index >= len(target_values) else "missing_response"
            if status == "right_censored":
                right_censored_count += 1
            else:
                missing_response_count += 1
            triggers.append(
                TriggerEvent(
                    source=source,
                    target=target,
                    trigger_index=trigger_index,
                    trigger_timestamp_seconds=timestamps[trigger_index],
                    previous_state=source_values[trigger_index - 1],
                    new_state=source_values[trigger_index],
                    status=status,
                )
            )
            continue

        delay = timestamps[response_index] - timestamps[trigger_index]
        response = ResponseEvent(
            source=source,
            target=target,
            trigger_index=trigger_index,
            response_index=response_index,
            trigger_timestamp_seconds=timestamps[trigger_index],
            response_timestamp_seconds=timestamps[response_index],
            delay_seconds=delay,
            magnitude=float(magnitude),
        )
        responses.append(response)
        triggers.append(
            TriggerEvent(
                source=source,
                target=target,
                trigger_index=trigger_index,
                trigger_timestamp_seconds=timestamps[trigger_index],
                previous_state=source_values[trigger_index - 1],
                new_state=source_values[trigger_index],
                status="matched",
                response_index=response.response_index,
                response_delay_seconds=response.delay_seconds,
                response_magnitude=response.magnitude,
            )
        )

    status = "supported" if len(responses) >= config.min_matched_response_count else "INSUFFICIENT_NORMAL_SUPPORT"
    config_hash = stable_hash({"relation_profiling_config": config.to_dict()})
    return RelationProfile(
        source=source,
        target=target,
        relation_type="binary_actuator_to_continuous_sensor",
        source_view=data_view.source_view or data_view.name.value,
        sampling_period_seconds=data_view.sampling_period_seconds,
        trigger_count=len(triggers),
        matched_response_count=len(responses),
        censored_or_missing_count=missing_response_count + right_censored_count,
        delay_summary_seconds=_summary([event.delay_seconds for event in responses]),
        magnitude_summary=_summary([event.magnitude for event in responses]),
        normal_support_status=status,
        upstream_artifact_ids=tuple(upstream_artifact_ids),
        dataset=dataset,
        split_name=split.role.value,
        data_fingerprint=data_fingerprint,
        config_hash=config_hash,
        code_commit=code_commit,
        random_seed=random_seed,
        created_at=created_at,
        trigger_events=tuple(triggers),
        response_events=tuple(responses),
        missing_response_count=missing_response_count,
        right_censored_count=right_censored_count,
        overlapping_window_count=overlapping_window_count,
    )


def calibrate_relation_profile(
    *,
    profile: RelationProfile,
    split: SplitManifest,
    config: RelationProfilingConfig,
) -> tuple[CalibrationRecord, ...]:
    """Derive deterministic rule parameters from a supported normal-data profile."""

    assert_split_permitted(split.role, "calibrate_rule_parameters")
    if profile.normal_support_status != "supported":
        raise RelationProfilingError("cannot calibrate an unsupported relation profile")
    delays = [event.delay_seconds for event in profile.response_events]
    magnitudes = [event.magnitude for event in profile.response_events]
    if len(delays) < config.min_matched_response_count or len(magnitudes) < config.min_matched_response_count:
        raise RelationProfilingError("insufficient matched responses for calibration")

    profile_id = profile.profile_id
    split_id = split.split_id
    return (
        CalibrationRecord(
            parameter_name="max_response_delay_seconds",
            value=_quantile(delays, config.delay_quantile),
            unit="seconds",
            method="empirical_linear_quantile",
            quantile_or_config={
                "quantile": config.delay_quantile,
                "max_response_delay_samples": config.max_response_delay_samples,
            },
            normal_support_count=len(delays),
            relation_profile_id=profile_id,
            calibration_split_id=split_id,
        ),
        CalibrationRecord(
            parameter_name="min_response_magnitude",
            value=_quantile(magnitudes, config.magnitude_quantile),
            unit="target_units",
            method="empirical_linear_quantile",
            quantile_or_config={
                "quantile": config.magnitude_quantile,
                "response_delta_floor": config.response_delta_floor,
            },
            normal_support_count=len(magnitudes),
            relation_profile_id=profile_id,
            calibration_split_id=split_id,
        ),
    )


def build_relation_evidence_pack(
    *,
    profile: RelationProfile,
    calibration_records: Sequence[CalibrationRecord],
) -> RelationEvidencePack:
    """Build an aggregate-only evidence pack for later template/LLM planners."""

    if profile.normal_support_status != "supported":
        raise RelationProfilingError("unsupported profiles cannot produce rule evidence packs")
    record_by_parameter = {record.parameter_name: record for record in calibration_records}
    required = {"max_response_delay_seconds", "min_response_magnitude"}
    if set(record_by_parameter) != required:
        raise RelationProfilingError("evidence pack requires delay and magnitude calibration records")
    if any(record.relation_profile_id != profile.profile_id for record in calibration_records):
        raise RelationProfilingError("calibration records must reference the supplied profile")

    return RelationEvidencePack(
        source=profile.source,
        target=profile.target,
        relation_type=profile.relation_type,
        recommended_rule_family="changed_to_increase_within_response_missing",
        relation_profile_id=profile.profile_id,
        calibration_record_ids={
            name: record_by_parameter[name].calibration_id for name in sorted(record_by_parameter)
        },
        calibrated_parameters={name: record_by_parameter[name].value for name in sorted(record_by_parameter)},
        support_counts={
            "trigger_count": profile.trigger_count,
            "matched_response_count": profile.matched_response_count,
            "missing_response_count": profile.missing_response_count,
            "right_censored_count": profile.right_censored_count,
            "overlapping_window_count": profile.overlapping_window_count,
        },
        source_view=profile.source_view,
        sampling_period_seconds=profile.sampling_period_seconds,
        upstream_artifact_ids=profile.upstream_artifact_ids,
    )


def _validate_supported_metadata(*, source: str, target: str, metadata: MetadataRegistry) -> None:
    source_meta = metadata.get(source)
    target_meta = metadata.get(target)
    if source_meta.role != VariableRole.ACTUATOR or source_meta.value_type != ValueType.BINARY:
        raise RelationProfilingError("source must be a binary actuator")
    if target_meta.role != VariableRole.SENSOR or target_meta.value_type != ValueType.CONTINUOUS:
        raise RelationProfilingError("target must be a continuous sensor")


def _validate_canonical_rule_view(data_view: DataViewManifest) -> None:
    if data_view.name != DataViewName.CANONICAL_RULE:
        raise RelationProfilingError("relation profiling requires the canonical rule view")
    if (data_view.source_view or data_view.name.value) != "canonical_rule_view":
        raise RelationProfilingError("relation profiling requires source_view=canonical_rule_view")


def _aligned_pair_series(
    series: Mapping[str, Sequence[float]],
    source: str,
    target: str,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if source not in series or target not in series:
        raise RelationProfilingError("series must contain source and target")
    source_values = tuple(float(item) for item in series[source])
    target_values = tuple(float(item) for item in series[target])
    if len(source_values) != len(target_values):
        raise RelationProfilingError("source and target series must have equal lengths")
    if len(source_values) < 2:
        raise RelationProfilingError("series must contain at least two samples")
    if any(not math.isfinite(item) for item in source_values + target_values):
        raise RelationProfilingError("series values must be finite")
    return source_values, target_values


def _timestamps(
    *,
    length: int,
    sampling_period_seconds: float,
    timestamps_seconds: Sequence[float] | None,
    config: RelationProfilingConfig,
) -> tuple[float, ...]:
    if timestamps_seconds is None:
        return tuple(index * sampling_period_seconds for index in range(length))
    timestamps = tuple(float(item) for item in timestamps_seconds)
    if len(timestamps) != length:
        raise RelationProfilingError("timestamps must match series length")
    if any(not math.isfinite(item) for item in timestamps):
        raise RelationProfilingError("timestamps must be finite")
    for previous, current in zip(timestamps, timestamps[1:]):
        observed = current - previous
        if observed <= 0:
            raise RelationProfilingError("timestamps must be strictly increasing")
        if abs(observed - sampling_period_seconds) > config.timestamp_tolerance_seconds:
            raise RelationProfilingError("irregular sampling rejected by policy")
    return timestamps


def _trigger_indexes(*, values: Sequence[float], trigger_from: float, trigger_to: float) -> tuple[int, ...]:
    indexes: list[int] = []
    for index in range(1, len(values)):
        if values[index - 1] == trigger_from and values[index] == trigger_to:
            indexes.append(index)
    return tuple(indexes)


def _summary(values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {}
    return {
        "count": float(len(values)),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "p50": _quantile(values, 0.5),
    }


def _quantile(values: Sequence[float], quantile: float) -> float:
    if not values:
        raise RelationProfilingError("cannot compute quantile over empty values")
    ordered = sorted(float(item) for item in values)
    if len(ordered) == 1:
        return ordered[0]
    position = quantile * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight
