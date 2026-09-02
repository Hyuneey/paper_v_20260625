"""Frozen scientific semantics for V2A EXP-02.

All functions are pure over caller-provided normal-only arrays.  The runner is
responsible for custody, split opening, private persistence, and public-safe
receipts.  This module has no label or evaluation-split adapter.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import inspect
import json
import math
from typing import Any, Mapping, Sequence

from paperworks.validation_v2.numeric_policy_v1 import (
    ConfirmedCohortAuthorityV1,
    NumericPolicyCandidateV1,
    NumericPolicySelectionSummaryV1,
    SplitNormalSummaryV1,
    build_numeric_policy_selection_summary_v1,
    build_split_normal_summary_v1,
    derive_pooled_role_values_v1,
    fit_split_variability_v1,
    NumericPolicyError,
)
from paperworks.validation_v2.formal_v4_authority_v1 import FormalV4AuthorityError
from paperworks.validation_v2.protocol_v1 import ValidationProtocolV1
from paperworks.validation_v2.runtime_v1 import (
    FormalV4PreparedParametersV1,
    evaluate_formal_v4_semantics_v1,
)
from paperworks.v6.continuous_step_protocol_v1 import (
    SustainedStepEventV1,
    cluster_step_events_v1,
)


EXP02_QUANTILES = (0.50, 0.75, 0.90)
EXP02_BINDING_IDS = (
    "EXP02-BIND-QUANTILE",
    "EXP02-BIND-RELATION-SUMMARY",
    "EXP02-BIND-OPPORTUNITY-CENSUS",
)
EXP02_CROSS_SOURCE_POLICY = (
    "CANDIDATE_SPECIFIC_RELATION_LOCAL_BOTH_DIRECTIONS_UNION_DEDUP_"
    "NEAREST_OTHER_PHYSICAL_SOURCE_TO_FORMAL_V4"
)


class Exp02BindingError(ValueError):
    pass


def _fail(code: str) -> None:
    raise Exp02BindingError(code)


def canonical_hash_v1(document: Mapping[str, Any]) -> str:
    return sha256(json.dumps(
        dict(document), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")).hexdigest()


def empirical_linear_quantiles_v1(
    values: Sequence[float],
) -> tuple[float, float, float]:
    """Exact deterministic q*(n-1) linear interpolation on positive values."""

    ordered = sorted(float(value) for value in values)
    if not ordered or any(not math.isfinite(value) or value <= 0.0 for value in ordered):
        _fail("EXP02_REQUIRED_AMPLITUDE_SET_EMPTY_OR_INVALID")
    result: list[float] = []
    for quantile in EXP02_QUANTILES:
        position = quantile * (len(ordered) - 1)
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            result.append(float(ordered[lower]))
        else:
            fraction = position - lower
            result.append(float(ordered[lower] + fraction * (ordered[upper] - ordered[lower])))
    return tuple(result)  # type: ignore[return-value]


def _finite_differences(values: Any) -> Any:
    import numpy as np

    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size < 2 or not bool(np.isfinite(array).all()):
        _fail("EXP02_SPLIT_SERIES_INVALID")
    return np.diff(array)


def build_relation_summaries_for_split_v1(
    *, split_id: str, matrix: Any, feature_order: Sequence[str],
    cohort: ConfirmedCohortAuthorityV1,
) -> tuple[SplitNormalSummaryV1, ...]:
    """Build one relation-local summary without cross-file differencing."""

    import numpy as np

    if split_id not in ("train1", "train2"):
        _fail("EXP02_SUMMARY_SPLIT_PROHIBITED")
    array = np.asarray(matrix, dtype=np.float64)
    order = tuple(feature_order)
    if array.ndim != 2 or array.shape[1] != len(order) or len(order) != len(set(order)):
        _fail("EXP02_SUMMARY_MATRIX_INVALID")
    if not bool(np.isfinite(array).all()):
        _fail("EXP02_SUMMARY_MATRIX_NONFINITE")
    positions = {name: index for index, name in enumerate(order)}
    cache: dict[str, tuple[Any, float, tuple[float, float, float]]] = {}
    for name in {item.source for item in cohort.relations} | {item.target for item in cohort.relations}:
        if name not in positions:
            _fail("EXP02_SUMMARY_FEATURE_MISSING")
        differences = _finite_differences(array[:, positions[name]])
        absolute = np.abs(differences)
        noise = float(np.median(absolute))
        nontrivial = absolute[absolute > 0.0]
        cache[name] = (differences, noise, empirical_linear_quantiles_v1(nontrivial.tolist()))
    summaries: list[SplitNormalSummaryV1] = []
    for relation in cohort.relations:
        source_differences, source_noise, source_quantiles = cache[relation.source]
        _target_differences, target_noise, _target_quantiles = cache[relation.target]
        directed = (
            source_differences[source_differences > 0.0]
            if relation.source_direction == "step_up"
            else -source_differences[source_differences < 0.0]
        )
        relation_quantiles = empirical_linear_quantiles_v1(directed.tolist())
        if target_noise <= 0.0 or not math.isfinite(target_noise):
            _fail("EXP02_TARGET_NOISE_NONPOSITIVE")
        summaries.append(build_split_normal_summary_v1(
            split_id=split_id,
            relation_id=relation.relation_id,
            source=relation.source,
            target=relation.target,
            source_scope_noise=float(source_noise),
            source_scope_quantiles=source_quantiles,
            target_scope_noise=float(target_noise),
            relation_noise=float(source_noise),
            relation_quantiles=relation_quantiles,
            relation_target_noise=float(target_noise),
        ))
    return tuple(sorted(summaries, key=lambda item: item.relation_id))


def extract_candidate_specific_events_v1(
    values: Any, *, threshold: float, tolerance: float,
) -> tuple[SustainedStepEventV1, ...]:
    """Vectorized implementation of the frozen 5/5 sustained-step scan."""

    import numpy as np

    series = np.asarray(values, dtype=np.float64)
    if series.ndim != 1 or series.size < 10 or not bool(np.isfinite(series).all()):
        _fail("EXP02_EVENT_SERIES_INVALID")
    if not math.isfinite(threshold) or threshold <= 0.0 or not math.isfinite(tolerance) or tolerance < 0.0:
        _fail("EXP02_EVENT_PARAMETER_INVALID")
    windows = np.lib.stride_tricks.sliding_window_view(series, 5)
    event_indices = np.arange(5, series.size - 4, dtype=np.int64)
    pre = windows[: event_indices.size]
    post = windows[5 : 5 + event_indices.size]
    pre_levels = np.median(pre, axis=1)
    post_levels = np.median(post, axis=1)
    amplitudes = post_levels - pre_levels
    pre_fractions = np.mean(np.abs(pre - pre_levels[:, None]) <= tolerance, axis=1)
    post_fractions = np.mean(np.abs(post - post_levels[:, None]) <= tolerance, axis=1)
    keep = (
        (amplitudes != 0.0)
        & (np.abs(amplitudes) >= threshold)
        & (pre_fractions >= 0.8)
        & (post_fractions >= 0.8)
    )
    events = tuple(
        SustainedStepEventV1(
            int(event_index),
            "step_up" if float(amplitude) > 0.0 else "step_down",
            float(pre_level), float(post_level), float(amplitude),
            float(pre_fraction), float(post_fraction),
        )
        for event_index, amplitude, pre_level, post_level, pre_fraction, post_fraction
        in zip(
            event_indices[keep], amplitudes[keep], pre_levels[keep], post_levels[keep],
            pre_fractions[keep], post_fractions[keep],
        )
    )
    return cluster_step_events_v1(events, refractory_seconds=10)


def _nearest_distance(index: int, ordered: tuple[int, ...]) -> float | None:
    if not ordered:
        return None
    position = bisect_left(ordered, index)
    candidates = []
    if position < len(ordered):
        candidates.append(abs(ordered[position] - index))
    if position:
        candidates.append(abs(ordered[position - 1] - index))
    return float(min(candidates))


def _parameters(values: tuple[tuple[str, float], ...]) -> FormalV4PreparedParametersV1:
    data = dict(values)
    required = {
        "minimum_source_stability_fraction", "source_step_threshold",
        "source_stability_tolerance", "target_noise_scale",
        "source_refractory_seconds", "cross_source_isolation_radius_seconds",
    }
    integer_roles = (
        "source_pre_window_seconds", "source_post_window_seconds",
        "target_baseline_window_seconds", "target_response_window_seconds",
    )
    if any(role not in data or data[role] <= 0.0 or not float(data[role]).is_integer() for role in integer_roles):
        _fail("EXP02_FORMAL_V4_WINDOW_PARAMETER_INVALID")
    if required - data.keys() or any(not math.isfinite(float(data[role])) for role in required):
        _fail("EXP02_FORMAL_V4_PARAMETER_MISSING_OR_NONFINITE")
    if not 0.0 < float(data["minimum_source_stability_fraction"]) <= 1.0:
        _fail("EXP02_FORMAL_V4_STABILITY_FRACTION_INVALID")
    if float(data["source_step_threshold"]) <= 0.0:
        _fail("EXP02_FORMAL_V4_THRESHOLD_INVALID")
    if float(data["source_stability_tolerance"]) < 0.0:
        _fail("EXP02_FORMAL_V4_TOLERANCE_INVALID")
    if float(data["target_noise_scale"]) <= 0.0:
        _fail("EXP02_FORMAL_V4_TARGET_SCALE_INVALID")
    if float(data["source_refractory_seconds"]) < 0.0 or float(data["cross_source_isolation_radius_seconds"]) < 0.0:
        _fail("EXP02_FORMAL_V4_DISTANCE_PARAMETER_INVALID")
    return FormalV4PreparedParametersV1(
        source_pre_count=int(data["source_pre_window_seconds"]),
        source_post_count=int(data["source_post_window_seconds"]),
        target_baseline_count=int(data["target_baseline_window_seconds"]),
        target_response_count=int(data["target_response_window_seconds"]),
        minimum_source_stability_fraction=float(data["minimum_source_stability_fraction"]),
        source_step_threshold=float(data["source_step_threshold"]),
        source_stability_tolerance=float(data["source_stability_tolerance"]),
        target_noise_scale=float(data["target_noise_scale"]),
        source_refractory_seconds=float(data["source_refractory_seconds"]),
        cross_source_isolation_radius_seconds=float(data["cross_source_isolation_radius_seconds"]),
    )


def _episode_count(seconds: set[int]) -> int:
    ordered = sorted(seconds)
    return sum(
        index == 0 or value != ordered[index - 1] + 1
        for index, value in enumerate(ordered)
    )


@dataclass(frozen=True)
class CandidateCensusV1:
    retained_relations: int
    opportunity_relations: int
    pass_count: int
    fail_count: int
    abstain_count: int
    unsupported_relation_count: int
    system_error_count: int
    false_alarm_seconds: int
    false_alarm_episodes: int
    normal_exposure_seconds: int
    split_variability: Fraction


def evaluate_candidate_on_train4_v1(
    *, candidate: NumericPolicyCandidateV1,
    cohort: ConfirmedCohortAuthorityV1,
    summaries_by_relation: Mapping[str, tuple[SplitNormalSummaryV1, SplitNormalSummaryV1]],
    train4_matrix: Any, feature_order: Sequence[str],
) -> CandidateCensusV1:
    """Candidate-specific census using the shared Formal V4 semantic kernel."""

    import numpy as np

    matrix = np.asarray(train4_matrix, dtype=np.float64)
    order = tuple(feature_order)
    if matrix.ndim != 2 or matrix.shape[1] != len(order) or not bool(np.isfinite(matrix).all()):
        _fail("EXP02_TRAIN4_MATRIX_INVALID")
    positions = {name: index for index, name in enumerate(order)}
    relation_parameters: dict[str, FormalV4PreparedParametersV1] = {}
    variability = Fraction(0, 1)
    unsupported = 0
    for relation in cohort.relations:
        summaries = summaries_by_relation.get(relation.relation_id)
        if summaries is None:
            unsupported += 1
            continue
        try:
            pooled = derive_pooled_role_values_v1(candidate=candidate, summaries=summaries)
            relation_parameters[relation.relation_id] = _parameters(pooled)
            variability = max(variability, fit_split_variability_v1(candidate=candidate, summaries=summaries))
        except (NumericPolicyError, Exp02BindingError, KeyError, TypeError, ValueError):
            unsupported += 1
    event_cache: dict[tuple[str, float, float], tuple[SustainedStepEventV1, ...]] = {}
    relation_events: dict[str, tuple[SustainedStepEventV1, ...]] = {}
    source_universe: dict[str, set[int]] = {}
    for relation in cohort.relations:
        parameters = relation_parameters.get(relation.relation_id)
        if parameters is None:
            continue
        key = (relation.source, parameters.source_step_threshold, parameters.source_stability_tolerance)
        if key not in event_cache:
            event_cache[key] = extract_candidate_specific_events_v1(
                matrix[:, positions[relation.source]], threshold=key[1], tolerance=key[2]
            )
        events = event_cache[key]
        relation_events[relation.relation_id] = events
        source_universe.setdefault(relation.source, set()).update(event.event_index for event in events)
    ordered_source_universe = {source: tuple(sorted(rows)) for source, rows in source_universe.items()}
    pass_count = fail_count = abstain_count = system_errors = 0
    opportunity_relations = 0
    fail_seconds: set[int] = set()
    for relation in cohort.relations:
        parameters = relation_parameters.get(relation.relation_id)
        if parameters is None:
            continue
        opportunities = tuple(
            event for event in relation_events[relation.relation_id]
            if event.direction == relation.source_direction
        )
        if opportunities:
            opportunity_relations += 1
        same_source = tuple(event.event_index for event in relation_events[relation.relation_id])
        other_rows = tuple(sorted(
            row for source, rows in ordered_source_universe.items()
            if source != relation.source for row in rows
        ))
        source_values = matrix[:, positions[relation.source]]
        target_values = matrix[:, positions[relation.target]]
        for event in opportunities:
            try:
                own_position = bisect_left(same_source, event.event_index)
                previous = None if own_position == 0 else float(event.event_index - same_source[own_position - 1])
                response_start = event.event_index + relation.selected_horizon_seconds
                response_end = response_start + parameters.target_response_count
                semantic = evaluate_formal_v4_semantics_v1(
                    source_direction=relation.source_direction,
                    target_direction=relation.target_direction,
                    parameters=parameters,
                    source_pre_values=tuple(float(x) for x in source_values[event.event_index - parameters.source_pre_count:event.event_index]),
                    source_post_values=tuple(float(x) for x in source_values[event.event_index:event.event_index + parameters.source_post_count]),
                    target_baseline_values=tuple(float(x) for x in target_values[event.event_index - parameters.target_baseline_count:event.event_index]),
                    target_response_values=tuple(float(x) for x in target_values[response_start:min(response_end, len(target_values))]),
                    seconds_since_previous_source_trigger=previous,
                    seconds_to_nearest_other_source_trigger=_nearest_distance(event.event_index, other_rows),
                    future_window_complete=response_end <= len(target_values),
                )
                if semantic.outcome == "PASS":
                    pass_count += 1
                elif semantic.outcome == "FAIL":
                    fail_count += 1
                    fail_seconds.add(response_end - 1)
                else:
                    abstain_count += 1
            except (FormalV4AuthorityError, ArithmeticError, IndexError, TypeError, ValueError):
                system_errors += 1
    return CandidateCensusV1(
        retained_relations=len(relation_parameters),
        opportunity_relations=opportunity_relations,
        pass_count=pass_count,
        fail_count=fail_count,
        abstain_count=abstain_count,
        unsupported_relation_count=unsupported,
        system_error_count=system_errors,
        false_alarm_seconds=len(fail_seconds),
        false_alarm_episodes=_episode_count(fail_seconds),
        normal_exposure_seconds=int(matrix.shape[0]),
        split_variability=variability,
    )


def build_selection_summary_from_census_v1(
    *, candidate: NumericPolicyCandidateV1, census: CandidateCensusV1,
    selection_authority: Any, protocol: ValidationProtocolV1,
) -> NumericPolicySelectionSummaryV1:
    return build_numeric_policy_selection_summary_v1(
        candidate=candidate, selection_authority=selection_authority, protocol=protocol,
        retained_relations=census.retained_relations,
        cohort_relations=selection_authority.cohort_relations,
        opportunity_relations=census.opportunity_relations,
        pass_count=census.pass_count, fail_count=census.fail_count,
        abstain_count=census.abstain_count,
        unsupported_relation_count=census.unsupported_relation_count,
        system_error_count=census.system_error_count,
        false_alarm_seconds=census.false_alarm_seconds,
        false_alarm_episodes=census.false_alarm_episodes,
        normal_exposure_seconds=census.normal_exposure_seconds,
        split_variability=census.split_variability,
    )


def binding_specifications_v1() -> dict[str, dict[str, Any]]:
    return {
        "EXP02-BIND-QUANTILE": {
            "scope": ["train1", "train2"], "cross_file_differencing": False,
            "quantiles": list(EXP02_QUANTILES), "method": "LINEAR_Q_TIMES_N_MINUS_1",
            "positive_amplitudes_only": True,
        },
        "EXP02-BIND-RELATION-SUMMARY": {
            "source_noise": "MEDIAN_ABS_FILE_LOCAL_FIRST_DIFFERENCE",
            "relation_noise": "EQUAL_SOURCE_SCOPE_NOISE",
            "target_noise": "MEDIAN_ABS_FILE_LOCAL_FIRST_DIFFERENCE",
            "relation_target_noise": "EQUAL_TARGET_SCOPE_NOISE",
            "direction_conditioned_amplitudes": True,
        },
        "EXP02-BIND-OPPORTUNITY-CENSUS": {
            "cross_source_trigger_universe": EXP02_CROSS_SOURCE_POLICY,
            "opportunity_formation": "CANDIDATE_SPECIFIC",
            "evaluator": "SHARED_FORMAL_V4_SEMANTIC_KERNEL",
            "false_second": "DECISION_PHYSICAL_ROW_SECOND",
            "episode": "MAXIMAL_ZERO_GAP_FILE_LOCAL",
        },
    }


def implementation_hashes_v1() -> dict[str, str]:
    return {
        "EXP02-BIND-QUANTILE": sha256(inspect.getsource(empirical_linear_quantiles_v1).encode()).hexdigest(),
        "EXP02-BIND-RELATION-SUMMARY": sha256(inspect.getsource(build_relation_summaries_for_split_v1).encode()).hexdigest(),
        "EXP02-BIND-OPPORTUNITY-CENSUS": sha256(inspect.getsource(evaluate_candidate_on_train4_v1).encode()).hexdigest(),
    }


__all__ = [
    "CandidateCensusV1", "EXP02_BINDING_IDS", "EXP02_CROSS_SOURCE_POLICY",
    "Exp02BindingError", "binding_specifications_v1",
    "build_relation_summaries_for_split_v1", "build_selection_summary_from_census_v1",
    "canonical_hash_v1", "empirical_linear_quantiles_v1",
    "evaluate_candidate_on_train4_v1", "extract_candidate_specific_events_v1",
    "implementation_hashes_v1",
]
