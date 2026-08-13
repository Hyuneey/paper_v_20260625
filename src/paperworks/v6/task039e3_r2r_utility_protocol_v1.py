"""Post-result, pre-label utility protocol for TASK-039E3 R2R.

This module is deliberately incapable of loading HAI rows or labels.  It
contains only closed metadata builders and synthetic, in-memory protocol
oracles.  It grants utility-evaluation authority only; it is not Rule v2,
production runtime, deployment, or winner authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Any, Mapping, Sequence

from paperworks.data.contracts_v2 import (
    CreationMetadataV2,
    DataViewKindV2,
    DataViewManifestV2,
    ProvenanceStatusV2,
    RawRangeV2,
    SealedAccessStatusV2,
    SplitManifestV2,
    SplitRoleV2,
)
from paperworks.data.splits_v2 import validate_split_collection_v2
from paperworks.v6.common import stable_hash_v1


TASK_ID = "TASK-039E3-R2R-UTILITY-PROTOCOL-FREEZE"
PROTOCOL_CLASSIFICATION = "POST_RESULT_PROTOCOL_FREEZE"
BASE_COMMIT = "cd6c23b68131820acf03d16cdd78c77db9635f59"
GATE_COMMIT_A = "4298daa03e209383040c0271a073e7fb7cdd0011"
GATE_COMMIT_B = BASE_COMMIT
GATE_BUNDLE_HASH = "803f4f6f614b587925bb974420ef93a2c97502a291dfe5443c3597556e78e57b"
GATE_RECEIPT_HASH = "110a0070f309db6680a508a6f10e65025f1c87b15585f8c019a3dbe277a48f02"

DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
SCIENTIFIC_P1_VIEW_ID = "d7bcc2b06aedd627db78a0dc104dd6fec5a171f0a2be773180e48ca3e8e52f57"
P1_FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
PROCESS_SCOPE = ("P1",)
SAMPLING_INTERVAL_SECONDS = 1.0

TEST1_OBSERVATIONS = 54_000
PURGE_GAP_SAMPLES = 120
TEST2_OBSERVATIONS = 230_400
TEST1_RANGE = (0, TEST1_OBSERVATIONS)
PURGE_RANGE = (TEST1_RANGE[1], TEST1_RANGE[1] + PURGE_GAP_SAMPLES)
TEST2_RANGE = (PURGE_RANGE[1], PURGE_RANGE[1] + TEST2_OBSERVATIONS)
LOGICAL_EXTENT = TEST2_RANGE[1]

SOURCE_PRE_WINDOW_SECONDS = 5
SOURCE_POST_WINDOW_SECONDS = 5
MINIMUM_SOURCE_STABILITY_FRACTION = 0.8
SOURCE_REFRACTORY_SECONDS = 10
CROSS_SOURCE_ISOLATION_RADIUS_SECONDS = 2
TARGET_BASELINE_WINDOW_SECONDS = 5
TARGET_RESPONSE_WINDOW_SECONDS = 3
SUPPORTED_HORIZONS_SECONDS = frozenset({1, 5, 10, 30, 60})

INTERPRETER_ID = "OFFLINE_CANDIDATE_UTILITY_INTERPRETER_V1"
RUNTIME_LOGIC_FAMILY = "missing_expected_delayed_response"

WINDOW_REFERENCE_ROLES = (
    "source_pre_window_seconds",
    "source_post_window_seconds",
    "minimum_source_stability_fraction",
    "source_refractory_seconds",
    "cross_source_isolation_radius_seconds",
    "target_baseline_window_seconds",
    "target_response_window_seconds",
)

ABSTENTION_REASONS = frozenset(
    {
        "insufficient_pre_window",
        "incomplete_post_hold_window",
        "incomplete_target_response_window",
        "nonfinite_source_window",
        "nonfinite_target_window",
        "file_boundary",
        "split_boundary",
    }
)


class UtilityProtocolError(ValueError):
    """Raised when the closed utility protocol is violated."""


@dataclass(frozen=True)
class ExecutableSignatureV1:
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_delay_horizon_seconds: int
    source_threshold_reference: str
    source_stability_reference: str
    target_scale_reference: str
    window_constant_references: tuple[tuple[str, str], ...]
    runtime_logic_family: str

    def __post_init__(self) -> None:
        if not self.source or not self.target or self.source == self.target:
            raise UtilityProtocolError("signature source and target must be distinct")
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise UtilityProtocolError("unsupported source direction")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise UtilityProtocolError("unsupported target direction")
        if self.selected_delay_horizon_seconds not in SUPPORTED_HORIZONS_SECONDS:
            raise UtilityProtocolError("unsupported response horizon")
        if self.runtime_logic_family != RUNTIME_LOGIC_FAMILY:
            raise UtilityProtocolError("unsupported runtime logic family")
        observed_roles = tuple(role for role, _ in self.window_constant_references)
        if observed_roles != WINDOW_REFERENCE_ROLES:
            raise UtilityProtocolError("window references are incomplete or out of order")
        references = (
            self.source_threshold_reference,
            self.source_stability_reference,
            self.target_scale_reference,
            *(reference for _, reference in self.window_constant_references),
        )
        if any(not reference for reference in references) or len(set(references)) != len(references):
            raise UtilityProtocolError("numeric references must be non-empty and unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_delay_horizon_seconds": self.selected_delay_horizon_seconds,
            "source_threshold_reference": self.source_threshold_reference,
            "source_stability_reference": self.source_stability_reference,
            "target_scale_reference": self.target_scale_reference,
            "window_constant_references": {
                role: reference for role, reference in self.window_constant_references
            },
            "runtime_logic_family": self.runtime_logic_family,
        }

    @property
    def semantic_execution_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExecutableSignatureV1":
        windows = value.get("window_constant_references")
        if not isinstance(windows, Mapping):
            raise UtilityProtocolError("window_constant_references must be a mapping")
        return cls(
            source=str(value["source"]),
            source_step_direction=str(value["source_step_direction"]),
            target=str(value["target"]),
            target_response_direction=str(value["target_response_direction"]),
            selected_delay_horizon_seconds=int(value["selected_delay_horizon_seconds"]),
            source_threshold_reference=str(value["source_threshold_reference"]),
            source_stability_reference=str(value["source_stability_reference"]),
            target_scale_reference=str(value["target_scale_reference"]),
            window_constant_references=tuple(
                (role, str(windows[role])) for role in WINDOW_REFERENCE_ROLES
            ),
            runtime_logic_family=str(value["runtime_logic_family"]),
        )


def build_utility_data_view_v2(
    source_view: DataViewManifestV2,
    *,
    creation_metadata: CreationMetadataV2,
) -> DataViewManifestV2:
    """Derive a metadata-only utility view without calibration authority."""

    if source_view.view_id != SCIENTIFIC_P1_VIEW_ID:
        raise UtilityProtocolError("scientific P1 preprocessing view differs")
    if source_view.source_dataset_manifest_id != DATASET_MANIFEST_ID:
        raise UtilityProtocolError("dataset authority differs")
    if source_view.process_scope != PROCESS_SCOPE:
        raise UtilityProtocolError("process scope differs")
    if source_view.sampling_interval_seconds != SAMPLING_INTERVAL_SECONDS:
        raise UtilityProtocolError("sampling interval differs")
    if source_view.feature_order_hash != P1_FEATURE_ORDER_HASH:
        raise UtilityProtocolError("P1 feature order differs")
    if source_view.view_kind is not DataViewKindV2.CANONICAL_RULE:
        raise UtilityProtocolError("canonical rule view required")
    return DataViewManifestV2(
        view_kind=source_view.view_kind,
        source_dataset_manifest_id=source_view.source_dataset_manifest_id,
        process_scope=source_view.process_scope,
        sampling_interval_seconds=source_view.sampling_interval_seconds,
        preprocessing_config=dict(source_view.preprocessing_config),
        aggregation=source_view.aggregation,
        feature_order_hash=source_view.feature_order_hash,
        second_level_rule_calibration_allowed=False,
        provenance_status=ProvenanceStatusV2.VERIFIED,
        creation_metadata=creation_metadata,
    )


def build_utility_split_manifests_v2(
    utility_view: DataViewManifestV2,
    *,
    creation_metadata: CreationMetadataV2,
) -> tuple[SplitManifestV2, SplitManifestV2]:
    """Build the deterministic file-level INNER and OUTER metadata splits."""

    if utility_view.second_level_rule_calibration_allowed:
        raise UtilityProtocolError("utility view may not calibrate rules")
    common = {
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "data_view_id": utility_view.view_id,
        "event_ids": None,
        "purge_gap_samples": PURGE_GAP_SAMPLES,
        "process_scope": PROCESS_SCOPE,
        "seed": None,
        "provenance_status": ProvenanceStatusV2.VERIFIED,
        "sealed_access_status": SealedAccessStatusV2.NOT_APPLICABLE,
        "split_before_windowing": True,
        "creation_metadata": creation_metadata,
    }
    inner = SplitManifestV2(
        role=SplitRoleV2.INNER_UTILITY,
        raw_ranges=(RawRangeV2(*TEST1_RANGE),),
        creation_policy="deterministic_file_index_test1_inner_before_labels_v1",
        **common,
    )
    outer = SplitManifestV2(
        role=SplitRoleV2.OUTER_VALIDATION,
        raw_ranges=(RawRangeV2(*TEST2_RANGE),),
        creation_policy="deterministic_file_index_test2_outer_before_labels_v1",
        **common,
    )
    validate_split_collection_v2(
        (inner, outer), window_size=61, maximum_required_lag=60
    )
    return inner, outer


@dataclass(frozen=True)
class SyntheticCandidateDecisionV1:
    status: str
    anomaly: bool | None
    decision_index: int | None
    abstention_reason: str | None = None

    def __post_init__(self) -> None:
        allowed = {"no_trigger", "expected_response", "anomaly", "abstain"}
        if self.status not in allowed:
            raise UtilityProtocolError("unknown synthetic decision status")
        if self.status == "abstain":
            if self.abstention_reason not in ABSTENTION_REASONS or self.anomaly is not None:
                raise UtilityProtocolError("invalid abstention")
        elif self.abstention_reason is not None:
            raise UtilityProtocolError("non-abstention cannot carry an abstention reason")


def decision_index_v1(event_index: int, horizon_seconds: int) -> int:
    if event_index < 0 or horizon_seconds not in SUPPORTED_HORIZONS_SECONDS:
        raise UtilityProtocolError("invalid event index or response horizon")
    return event_index + horizon_seconds + TARGET_RESPONSE_WINDOW_SECONDS - 1


def _finite(values: Sequence[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def evaluate_synthetic_rule_window_v1(
    *,
    event_index: int,
    horizon_seconds: int,
    source_pre_window: Sequence[float],
    source_post_window: Sequence[float],
    target_baseline_window: Sequence[float],
    target_response_window: Sequence[float],
    expected_source_direction: str,
    expected_target_direction: str,
    source_step_threshold: float,
    source_stability_tolerance: float,
    target_noise_scale: float,
    isolated_source_event: bool = True,
) -> SyntheticCandidateDecisionV1:
    """Evaluate one explicitly synthetic, already-bounded rule opportunity."""

    if len(source_pre_window) < SOURCE_PRE_WINDOW_SECONDS:
        return SyntheticCandidateDecisionV1("abstain", None, None, "insufficient_pre_window")
    if len(source_post_window) < SOURCE_POST_WINDOW_SECONDS:
        return SyntheticCandidateDecisionV1("abstain", None, None, "incomplete_post_hold_window")
    if len(target_baseline_window) < TARGET_BASELINE_WINDOW_SECONDS:
        return SyntheticCandidateDecisionV1("abstain", None, None, "insufficient_pre_window")
    if len(target_response_window) < TARGET_RESPONSE_WINDOW_SECONDS:
        return SyntheticCandidateDecisionV1(
            "abstain", None, None, "incomplete_target_response_window"
        )
    source_required = tuple(source_pre_window[-5:]) + tuple(source_post_window[:5])
    target_required = tuple(target_baseline_window[-5:]) + tuple(target_response_window[:3])
    if not _finite(source_required):
        return SyntheticCandidateDecisionV1("abstain", None, None, "nonfinite_source_window")
    if not _finite(target_required):
        return SyntheticCandidateDecisionV1("abstain", None, None, "nonfinite_target_window")
    if expected_source_direction not in {"step_up", "step_down"}:
        raise UtilityProtocolError("unsupported source direction")
    if expected_target_direction not in {"increase", "decrease"}:
        raise UtilityProtocolError("unsupported target direction")
    if horizon_seconds not in SUPPORTED_HORIZONS_SECONDS:
        raise UtilityProtocolError("unsupported response horizon")
    if source_step_threshold <= 0 or source_stability_tolerance < 0 or target_noise_scale <= 0:
        raise UtilityProtocolError("synthetic thresholds are outside the frozen domain")
    pre_level = float(statistics.median(source_required[:5]))
    post_level = float(statistics.median(source_required[5:]))
    amplitude = post_level - pre_level
    direction = "step_up" if amplitude > 0 else "step_down"
    if amplitude == 0 or abs(amplitude) < source_step_threshold or direction != expected_source_direction:
        return SyntheticCandidateDecisionV1("no_trigger", False, None)
    pre_fraction = sum(abs(float(value) - pre_level) <= source_stability_tolerance for value in source_required[:5]) / 5.0
    post_fraction = sum(abs(float(value) - post_level) <= source_stability_tolerance for value in source_required[5:]) / 5.0
    if pre_fraction < MINIMUM_SOURCE_STABILITY_FRACTION or post_fraction < MINIMUM_SOURCE_STABILITY_FRACTION:
        return SyntheticCandidateDecisionV1("no_trigger", False, None)
    if not isolated_source_event:
        return SyntheticCandidateDecisionV1("no_trigger", False, None)
    baseline = float(statistics.median(target_required[:5]))
    response = float(statistics.median(target_required[5:])) - baseline
    matches = response > target_noise_scale if expected_target_direction == "increase" else response < -target_noise_scale
    decision = decision_index_v1(event_index, horizon_seconds)
    return SyntheticCandidateDecisionV1(
        "expected_response" if matches else "anomaly",
        not matches,
        decision,
    )


def cluster_synthetic_source_candidates_v1(
    candidates: Sequence[tuple[int, float]],
) -> tuple[tuple[int, float], ...]:
    ordered = sorted((int(index), float(amplitude)) for index, amplitude in candidates)
    if not ordered:
        return ()
    clusters: list[list[tuple[int, float]]] = [[ordered[0]]]
    for candidate in ordered[1:]:
        if candidate[0] - clusters[-1][-1][0] <= SOURCE_REFRACTORY_SECONDS:
            clusters[-1].append(candidate)
        else:
            clusters.append([candidate])
    return tuple(
        min(cluster, key=lambda item: (-abs(item[1]), item[0])) for cluster in clusters
    )


def is_synthetic_event_isolated_v1(
    *,
    source: str,
    event_index: int,
    retained_events_by_source: Mapping[str, Sequence[int]],
    required_sources: Sequence[str],
) -> bool:
    if set(retained_events_by_source) != set(required_sources):
        raise UtilityProtocolError("all frozen source streams are required")
    if source not in retained_events_by_source:
        raise UtilityProtocolError("event source is missing")
    return not any(
        abs(event_index - int(other_index)) <= CROSS_SOURCE_ISOLATION_RADIUS_SECONDS
        for other_source, indices in retained_events_by_source.items()
        if other_source != source
        for other_index in indices
    )


@dataclass(frozen=True)
class IntervalV1:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise UtilityProtocolError("interval must satisfy 0 <= start < end")


def derive_synthetic_attack_events_v1(labels: Sequence[int]) -> tuple[IntervalV1, ...]:
    values = tuple(int(value) for value in labels)
    if any(value not in {0, 1} for value in values):
        raise UtilityProtocolError("synthetic labels must be binary")
    result: list[IntervalV1] = []
    start: int | None = None
    for index, value in enumerate((*values, 0)):
        if value == 1 and start is None:
            start = index
        elif value == 0 and start is not None:
            result.append(IntervalV1(start, index))
            start = None
    return tuple(result)


def form_alarm_episodes_v1(raw_alarm_timestamps: Sequence[int]) -> tuple[IntervalV1, ...]:
    unique = sorted(set(int(item) for item in raw_alarm_timestamps))
    if any(item < 0 for item in unique):
        raise UtilityProtocolError("alarm timestamps must be non-negative")
    if not unique:
        return ()
    result: list[IntervalV1] = []
    start = previous = unique[0]
    for item in unique[1:]:
        if item == previous + 1:
            previous = item
            continue
        result.append(IntervalV1(start, previous + 1))
        start = previous = item
    result.append(IntervalV1(start, previous + 1))
    return tuple(result)


def intervals_overlap_v1(left: IntervalV1, right: IntervalV1) -> bool:
    return left.start < right.end and right.start < left.end


@dataclass(frozen=True)
class MetricValueV1:
    value: float | None
    numerator: int
    denominator: float
    defined: bool
    undefined_reason: str | None = None

    def __post_init__(self) -> None:
        if self.denominator < 0 or self.numerator < 0:
            raise UtilityProtocolError("metric counts must be non-negative")
        if self.defined != (self.value is not None):
            raise UtilityProtocolError("defined flag and value disagree")
        if self.defined == (self.undefined_reason is not None):
            raise UtilityProtocolError("undefined reason disagrees with metric state")


def _ratio(numerator: int, denominator: float, reason: str) -> MetricValueV1:
    if denominator == 0:
        return MetricValueV1(None, numerator, denominator, False, reason)
    return MetricValueV1(numerator / denominator, numerator, denominator, True, None)


def attack_event_recall_v1(
    attack_events: Sequence[IntervalV1], alarm_episodes: Sequence[IntervalV1]
) -> MetricValueV1:
    covered = sum(
        any(intervals_overlap_v1(event, alarm) for alarm in alarm_episodes)
        for event in attack_events
    )
    return _ratio(covered, len(attack_events), "no_attack_events")


def alarm_episode_precision_v1(
    attack_events: Sequence[IntervalV1], alarm_episodes: Sequence[IntervalV1]
) -> MetricValueV1:
    overlapping = sum(
        any(intervals_overlap_v1(event, alarm) for event in attack_events)
        for alarm in alarm_episodes
    )
    return _ratio(overlapping, len(alarm_episodes), "no_alarm_episodes")


def normal_false_alarm_rate_per_hour_v1(
    attack_events: Sequence[IntervalV1],
    alarm_episodes: Sequence[IntervalV1],
    *,
    normal_labeled_seconds: int,
) -> MetricValueV1:
    false_alarms = sum(
        not any(intervals_overlap_v1(event, alarm) for event in attack_events)
        for alarm in alarm_episodes
    )
    return _ratio(false_alarms, normal_labeled_seconds / 3600.0, "no_normal_exposure")


def event_f1_v1(precision: MetricValueV1, recall: MetricValueV1) -> MetricValueV1:
    if not precision.defined or not recall.defined:
        return MetricValueV1(None, 0, 0.0, False, "precision_or_recall_undefined")
    assert precision.value is not None and recall.value is not None
    denominator = precision.value + recall.value
    value = 0.0 if denominator == 0 else 2.0 * precision.value * recall.value / denominator
    return MetricValueV1(value, 0, 1.0, True, None)


def duplicate_firing_ratio_v1(raw_alarm_count: int, unique_alarm_timestamp_count: int) -> MetricValueV1:
    if unique_alarm_timestamp_count > raw_alarm_count:
        raise UtilityProtocolError("unique alarm count exceeds raw alarm count")
    return _ratio(
        raw_alarm_count - unique_alarm_timestamp_count,
        raw_alarm_count,
        "no_raw_rule_alarms",
    )


def no_rule_contribution_v1() -> dict[str, Any]:
    return {
        "interpreter_instances": 0,
        "runtime_evaluations": 0,
        "alarms": 0,
        "abstentions": 0,
        "construction_coverage": 0,
        "relation_denominator_contribution": 1,
        "attack_event_recall_contribution": 0,
        "false_alarm_count": 0,
        "alarm_precision": None,
    }


def exact_mcnemar_two_sided_v1(first_only: int, second_only: int) -> float | None:
    if first_only < 0 or second_only < 0:
        raise UtilityProtocolError("discordant counts must be non-negative")
    discordant = first_only + second_only
    if discordant == 0:
        return None
    smaller = min(first_only, second_only)
    tail = sum(math.comb(discordant, index) for index in range(smaller + 1)) / (2**discordant)
    return min(1.0, 2.0 * tail)


def protocol_policy_snapshot_v1() -> dict[str, Any]:
    """Return the closed, label-free governance summary committed by source."""

    return {
        "task_id": TASK_ID,
        "protocol_classification": PROTOCOL_CLASSIFICATION,
        "interpreter": INTERPRETER_ID,
        "interpreter_authority": "UTILITY_EVALUATION_ONLY",
        "primary_units": ["attack_event", "normal_exposure_hour"],
        "primary_metrics": ["attack_event_recall", "normal_false_alarm_rate_per_hour"],
        "point_adjustment": "PROHIBITED",
        "auroc": "NOT_APPLICABLE_TO_BINARY_EVENT_TRIGGERED_OUTPUT",
        "auprc": "NOT_APPLICABLE_TO_BINARY_EVENT_TRIGGERED_OUTPUT",
        "decision_index_formula": "event_index + selected_horizon_seconds + 2",
        "no_op_selection": "DEFERRED",
        "detector_integration": "DEFERRED_UNTIL_DETECTOR_PROTOCOL",
        "label_tuned_threshold_count": 0,
        "direct_number_threshold_substitution": False,
        "inner_file": "hai-test1.csv",
        "outer_file": "hai-test2.csv",
        "sealed_evaluation": "NOT_MATERIALIZED_NOT_AUTHORIZED",
        "rule_v2_authority": False,
        "production_runtime_authority": False,
        "deployment_authority": False,
        "winner_authority": False,
        "provider_authority": False,
        "utility_execution_authority": False,
        "label_values_accessed": False,
        "hai_test_feature_values_accessed": False,
        "utility_values_computed": False,
    }


__all__ = [
    "ABSTENTION_REASONS",
    "ExecutableSignatureV1",
    "IntervalV1",
    "MetricValueV1",
    "SyntheticCandidateDecisionV1",
    "UtilityProtocolError",
    "alarm_episode_precision_v1",
    "attack_event_recall_v1",
    "build_utility_data_view_v2",
    "build_utility_split_manifests_v2",
    "cluster_synthetic_source_candidates_v1",
    "decision_index_v1",
    "derive_synthetic_attack_events_v1",
    "duplicate_firing_ratio_v1",
    "evaluate_synthetic_rule_window_v1",
    "event_f1_v1",
    "exact_mcnemar_two_sided_v1",
    "form_alarm_episodes_v1",
    "is_synthetic_event_isolated_v1",
    "no_rule_contribution_v1",
    "normal_false_alarm_rate_per_hour_v1",
    "protocol_policy_snapshot_v1",
]
