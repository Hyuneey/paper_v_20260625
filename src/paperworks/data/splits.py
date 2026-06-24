"""Leakage-safe split and window utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from paperworks.data.contracts import (
    ContractError,
    DataViewManifest,
    DataViewName,
    DatasetManifest,
    SplitManifest,
    SplitRole,
    stable_hash,
)


class SplitPermissionError(PermissionError):
    """Raised when a split role is used for a prohibited operation."""


class SplitRangeError(ValueError):
    """Raised when raw split ranges overlap or cannot satisfy purge rules."""


PERMITTED_OPERATIONS: Mapping[str, set[SplitRole]] = {
    "train_candidate_learner": {SplitRole.TRAIN_NORMAL},
    "fit_scaler": {SplitRole.TRAIN_NORMAL},
    "profile_relation": {SplitRole.CALIBRATION_NORMAL},
    "calibrate_rule_parameters": {SplitRole.CALIBRATION_NORMAL},
    "verify_rule": {SplitRole.VALIDATION},
    "refine_rule": {SplitRole.VALIDATION},
    "final_evaluate": {SplitRole.TEST},
}


@dataclass(frozen=True)
class WindowSpec:
    input_start: int
    input_end: int
    target_index: int

    def __post_init__(self) -> None:
        if self.input_start < 0 or self.input_end <= self.input_start:
            raise SplitRangeError("invalid input window")
        if self.target_index < self.input_end:
            raise SplitRangeError("target_index must be at or after input_end")


def assert_split_permitted(role: SplitRole, operation: str) -> None:
    allowed = PERMITTED_OPERATIONS.get(operation)
    if allowed is None:
        raise SplitPermissionError(f"unknown operation: {operation}")
    if role not in allowed:
        allowed_values = ", ".join(sorted(item.value for item in allowed))
        raise SplitPermissionError(
            f"split role {role.value!r} is not permitted for {operation!r}; "
            f"allowed: {allowed_values}"
        )


def assert_no_overlapping_ranges(ranges: Sequence[tuple[int, int]]) -> None:
    previous_end: int | None = None
    for start, end in sorted(ranges):
        if start < 0 or end <= start:
            raise SplitRangeError(f"invalid range: {(start, end)}")
        if previous_end is not None and start < previous_end:
            raise SplitRangeError("raw ranges overlap")
        previous_end = end


def required_purge_gap(window_size: int, max_lag_samples: int = 0) -> int:
    if window_size <= 0:
        raise SplitRangeError("window_size must be positive")
    if max_lag_samples < 0:
        raise SplitRangeError("max_lag_samples must be non-negative")
    return window_size - 1 + max_lag_samples


def build_data_view_manifest(
    dataset_manifest: DatasetManifest,
    *,
    name: DataViewName = DataViewName.CANONICAL_RULE,
    sampling_period_seconds: float | None = None,
    preprocessing_config: Mapping[str, object] | None = None,
    source_view: str | None = None,
) -> DataViewManifest:
    config = dict(preprocessing_config or {})
    period = sampling_period_seconds or dataset_manifest.sampling_period_seconds
    payload = {
        "dataset_manifest_id": dataset_manifest.manifest_id,
        "name": name.value,
        "sampling_period_seconds": period,
        "preprocessing_config": config,
        "source_view": source_view or ("canonical_rule_view" if name == DataViewName.CANONICAL_RULE else name.value),
    }
    return DataViewManifest(
        name=name,
        sampling_period_seconds=period,
        preprocessing_config=config,
        upstream_dataset_manifest_id=dataset_manifest.manifest_id,
        fingerprint=stable_hash(payload),
        source_view=str(payload["source_view"]),
    )


def build_sequential_split_manifests(
    *,
    total_length: int,
    role_lengths: Sequence[tuple[SplitRole, int]],
    dataset_manifest_id: str,
    data_view_id: str,
    purge_gap_samples: int,
    seed: int | None,
) -> tuple[SplitManifest, ...]:
    if total_length <= 0:
        raise SplitRangeError("total_length must be positive")
    if purge_gap_samples < 0:
        raise SplitRangeError("purge_gap_samples must be non-negative")
    cursor = 0
    manifests: list[SplitManifest] = []
    for index, (role, length) in enumerate(role_lengths):
        if length <= 0:
            raise SplitRangeError("split lengths must be positive")
        start = cursor
        end = start + length
        if end > total_length:
            raise SplitRangeError("split lengths exceed total length")
        manifests.append(
            SplitManifest(
                dataset_manifest_id=dataset_manifest_id,
                data_view_id=data_view_id,
                role=role,
                raw_index_ranges=((start, end),),
                purge_gap_samples=purge_gap_samples,
                seed=seed,
            )
        )
        cursor = end + (purge_gap_samples if index < len(role_lengths) - 1 else 0)
    return tuple(manifests)


def generate_split_windows(
    split: SplitManifest,
    *,
    window_size: int,
    horizon: int = 1,
    step: int = 1,
) -> tuple[WindowSpec, ...]:
    if window_size <= 0 or horizon <= 0 or step <= 0:
        raise SplitRangeError("window_size, horizon, and step must be positive")
    windows: list[WindowSpec] = []
    for start, end in split.raw_index_ranges:
        target = start + window_size
        last_target = end - horizon
        while target <= last_target:
            input_start = target - window_size
            input_end = target
            if input_start < start or target >= end:
                raise ContractError("generated window crossed a split boundary")
            windows.append(WindowSpec(input_start, input_end, target))
            target += step
    return tuple(windows)

