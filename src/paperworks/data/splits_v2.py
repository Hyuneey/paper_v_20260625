"""Dataset-neutral v2 split permissions, purge checks, and windows."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from paperworks.data.contracts_v2 import (
    RawRangeV2,
    SealedAccessStatusV2,
    SplitManifestV2,
    SplitRoleV2,
)


class SplitPolicyV2Error(ValueError):
    """Raised when v2 split construction or windowing is invalid."""


class SplitPermissionV2Error(PermissionError):
    """Raised when an operation is not authorized for a v2 split."""


class DataOperationV2(str, Enum):
    FIT_CANDIDATE_LEARNER = "fit_candidate_learner"
    FIT_CANDIDATE_RANKER = "fit_candidate_ranker"
    PROFILE_NORMAL_RELATION = "profile_normal_relation"
    CALIBRATE_RELATION_PARAMETERS = "calibrate_relation_parameters"
    EVALUATE_NORMAL_GUARD = "evaluate_normal_guard"
    RUN_DEVELOPMENT_DIAGNOSTIC = "run_development_diagnostic"
    REVISE_RULE_WITH_FEEDBACK = "revise_rule_with_feedback"
    ASSESS_RULE_UTILITY = "assess_rule_utility"
    SELECT_RULE_OR_NO_OP = "select_rule_or_no_op"
    REPLAY_OUTER = "replay_outer"
    RUN_SEALED_EVALUATION = "run_sealed_evaluation"


OPERATION_PERMISSIONS_V2: Mapping[DataOperationV2, frozenset[SplitRoleV2]] = {
    DataOperationV2.FIT_CANDIDATE_LEARNER: frozenset(
        {SplitRoleV2.NORMAL_CANDIDATE_FIT}
    ),
    DataOperationV2.FIT_CANDIDATE_RANKER: frozenset(
        {SplitRoleV2.NORMAL_CANDIDATE_FIT}
    ),
    DataOperationV2.PROFILE_NORMAL_RELATION: frozenset(
        {SplitRoleV2.NORMAL_RELATION_CALIBRATION}
    ),
    DataOperationV2.CALIBRATE_RELATION_PARAMETERS: frozenset(
        {SplitRoleV2.NORMAL_RELATION_CALIBRATION}
    ),
    DataOperationV2.EVALUATE_NORMAL_GUARD: frozenset({SplitRoleV2.NORMAL_GUARD}),
    DataOperationV2.RUN_DEVELOPMENT_DIAGNOSTIC: frozenset(
        {SplitRoleV2.DEVELOPMENT}
    ),
    DataOperationV2.REVISE_RULE_WITH_FEEDBACK: frozenset(
        {SplitRoleV2.INNER_UTILITY}
    ),
    DataOperationV2.ASSESS_RULE_UTILITY: frozenset({SplitRoleV2.INNER_UTILITY}),
    DataOperationV2.SELECT_RULE_OR_NO_OP: frozenset({SplitRoleV2.INNER_UTILITY}),
    DataOperationV2.REPLAY_OUTER: frozenset({SplitRoleV2.OUTER_VALIDATION}),
    DataOperationV2.RUN_SEALED_EVALUATION: frozenset(
        {SplitRoleV2.SEALED_EVALUATION}
    ),
}


@dataclass(frozen=True)
class WindowSpecV2:
    range_index: int
    context_start: int
    input_start: int
    input_end: int
    target_index: int

    def __post_init__(self) -> None:
        if self.range_index < 0:
            raise SplitPolicyV2Error("range_index must be non-negative")
        if not (
            0 <= self.context_start <= self.input_start < self.input_end <= self.target_index
        ):
            raise SplitPolicyV2Error("invalid v2 window bounds")


def assert_operation_permitted_v2(
    split: SplitManifestV2,
    operation: DataOperationV2 | str,
) -> None:
    """Fail closed unless the split and sealed status authorize the operation."""

    try:
        typed_operation = (
            operation
            if isinstance(operation, DataOperationV2)
            else DataOperationV2(operation)
        )
    except ValueError as exc:
        raise SplitPermissionV2Error(f"unknown operation: {operation}") from exc
    allowed = OPERATION_PERMISSIONS_V2[typed_operation]
    if split.role not in allowed:
        allowed_values = ", ".join(sorted(item.value for item in allowed))
        raise SplitPermissionV2Error(
            f"split role {split.role.value!r} is not permitted for "
            f"{typed_operation.value!r}; allowed: {allowed_values}"
        )
    if (
        typed_operation is DataOperationV2.RUN_SEALED_EVALUATION
        and split.sealed_access_status is not SealedAccessStatusV2.APPROVED
    ):
        raise SplitPermissionV2Error("sealed evaluation requires explicit approval")


def required_purge_gap_v2(
    window_size: int,
    maximum_required_lag: int = 0,
) -> int:
    """Return the minimum split boundary purge required by v6."""

    if window_size <= 0:
        raise SplitPolicyV2Error("window_size must be positive")
    if maximum_required_lag < 0:
        raise SplitPolicyV2Error("maximum_required_lag must be non-negative")
    return window_size - 1 + maximum_required_lag


def validate_raw_ranges_v2(ranges: Sequence[RawRangeV2]) -> None:
    """Validate supplied order without sorting or silently repairing ranges."""

    if not ranges:
        raise SplitPolicyV2Error("at least one raw range is required")
    previous_end: int | None = None
    for item in ranges:
        if previous_end is not None and item.start < previous_end:
            raise SplitPolicyV2Error("raw ranges must be ordered and non-overlapping")
        previous_end = item.end


def assert_purge_gap_sufficient_v2(
    split: SplitManifestV2,
    *,
    window_size: int,
    maximum_required_lag: int = 0,
) -> None:
    required = required_purge_gap_v2(window_size, maximum_required_lag)
    if split.purge_gap_samples < required:
        raise SplitPolicyV2Error(
            f"purge gap {split.purge_gap_samples} is below required {required}"
        )


def validate_split_collection_v2(
    splits: Sequence[SplitManifestV2],
    *,
    window_size: int,
    maximum_required_lag: int = 0,
) -> None:
    """Validate split identity, ordering, and physical gaps before windowing."""

    if not splits:
        raise SplitPolicyV2Error("split collection must not be empty")
    expected_dataset = splits[0].dataset_manifest_id
    expected_view = splits[0].data_view_id
    required = required_purge_gap_v2(window_size, maximum_required_lag)
    flattened: list[tuple[int, int, str]] = []
    for split in splits:
        if split.dataset_manifest_id != expected_dataset or split.data_view_id != expected_view:
            raise SplitPolicyV2Error("all splits must reference one dataset and view")
        assert_purge_gap_sufficient_v2(
            split,
            window_size=window_size,
            maximum_required_lag=maximum_required_lag,
        )
        validate_raw_ranges_v2(split.raw_ranges)
        flattened.extend((item.start, item.end, split.split_id) for item in split.raw_ranges)
    flattened.sort(key=lambda item: item[0])
    for previous, current in zip(flattened, flattened[1:]):
        if current[0] < previous[1]:
            raise SplitPolicyV2Error("raw ranges overlap across split manifests")
        if current[2] != previous[2] and current[0] - previous[1] < required:
            raise SplitPolicyV2Error("physical split boundary purge is insufficient")


def generate_split_windows_v2(
    split: SplitManifestV2,
    *,
    window_size: int,
    maximum_required_lag: int = 0,
    horizon: int = 1,
    step: int = 1,
) -> tuple[WindowSpecV2, ...]:
    """Generate independent windows inside each already-frozen raw range."""

    if horizon <= 0 or step <= 0:
        raise SplitPolicyV2Error("horizon and step must be positive")
    assert_purge_gap_sufficient_v2(
        split,
        window_size=window_size,
        maximum_required_lag=maximum_required_lag,
    )
    validate_raw_ranges_v2(split.raw_ranges)
    windows: list[WindowSpecV2] = []
    for range_index, item in enumerate(split.raw_ranges):
        target = item.start + maximum_required_lag + window_size
        last_target = item.end - horizon
        while target <= last_target:
            input_start = target - window_size
            context_start = input_start - maximum_required_lag
            if context_start < item.start or target >= item.end:
                raise SplitPolicyV2Error("generated window crossed a raw-range boundary")
            windows.append(
                WindowSpecV2(
                    range_index=range_index,
                    context_start=context_start,
                    input_start=input_start,
                    input_end=target,
                    target_index=target,
                )
            )
            target += step
    return tuple(windows)
