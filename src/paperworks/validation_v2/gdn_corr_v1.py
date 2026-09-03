"""Prospective corrections and HAI-readiness primitives for GDN-CORR-001.

The frozen EXP-01B-V1 implementation intentionally remains unchanged.  This
module contains the separately versioned EXP-01B-R1 ranking/control semantics
and data-only diagnostics used to preregister EXP-01C.  All functions are pure
over caller-provided normal-only values; the module has no split or label I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any, Iterable, Mapping, Sequence

from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE
from paperworks.v6.common import stable_hash_v1


Pair = tuple[str, str]
R1_EDGE_TOLERANCE = 1e-12


class GDNCorrError(ValueError):
    """Fail-closed GDN corrective-analysis error."""


def _pairs(values: Iterable[Pair]) -> tuple[Pair, ...]:
    rows = tuple((str(source), str(target)) for source, target in values)
    if len(rows) != len(set(rows)) or any(pair not in PAIR_UNIVERSE for pair in rows):
        raise GDNCorrError("pair identities must be unique members of the 144-pair universe")
    return rows


def observed_percentiles_r1(
    scores: Mapping[Pair, float], *, target_local: bool,
) -> dict[Pair, float]:
    """Give every observed item positive, tie-aware percentile evidence.

    Within each requested ranking group, a raw-score tie receives the first
    zero-based rank index of that tie group and therefore the same scientific
    evidence.  Lexical pair identity is used only to make display order stable.
    Absent items remain exactly zero.
    """

    if any(pair not in PAIR_UNIVERSE for pair in scores):
        raise GDNCorrError("score map exceeds the frozen pair universe")
    normalized = {pair: float(value) for pair, value in scores.items()}
    if any(not math.isfinite(value) for value in normalized.values()):
        raise GDNCorrError("scores must be finite")
    result = {pair: 0.0 for pair in PAIR_UNIVERSE}
    groups: dict[str, list[tuple[Pair, float]]] = {}
    for pair, score in normalized.items():
        groups.setdefault(pair[1] if target_local else "ALL", []).append((pair, score))
    for rows in groups.values():
        ordered = sorted(rows, key=lambda row: (-row[1], row[0]))
        count = len(ordered)
        if count <= 0:
            continue
        first_index_by_score: dict[float, int] = {}
        for index, (_, score) in enumerate(ordered):
            first_index_by_score.setdefault(score, index)
        for pair, score in ordered:
            result[pair] = (count - first_index_by_score[score]) / count
    return result


def ranking_membership_percentiles_r1(ranking: Sequence[Pair]) -> dict[Pair, float]:
    """Represent observed ordered arm membership without a zero collision."""

    ordered = _pairs(ranking)
    if not ordered:
        raise GDNCorrError("ranking must not be empty")
    count = len(ordered)
    result = {pair: 0.0 for pair in PAIR_UNIVERSE}
    for index, pair in enumerate(ordered):
        result[pair] = (count - index) / count
    return result


def deterministic_ranking_r1(scores: Mapping[Pair, float]) -> tuple[Pair, ...]:
    if set(scores) != set(PAIR_UNIVERSE):
        raise GDNCorrError("deterministic ranking requires the complete universe")
    if any(not math.isfinite(float(value)) for value in scores.values()):
        raise GDNCorrError("deterministic ranking scores must be finite")
    return tuple(sorted(PAIR_UNIVERSE, key=lambda pair: (-float(scores[pair]), pair)))


@dataclass(frozen=True)
class SignedEdgeMaskEvidenceR1:
    positive_scores: Mapping[Pair, float]
    neutral_pairs: tuple[Pair, ...]
    counterevidence_pairs: tuple[Pair, ...]
    tolerance: float = R1_EDGE_TOLERANCE


def signed_edgemask_evidence_r1(
    raw_scores: Mapping[Pair, float], *, tolerance: float = R1_EDGE_TOLERANCE,
) -> SignedEdgeMaskEvidenceR1:
    """Separate positive functional evidence from neutral/counterevidence."""

    if tolerance != R1_EDGE_TOLERANCE:
        raise GDNCorrError("EXP-01B-R1 EdgeMask tolerance is frozen")
    positive: dict[Pair, float] = {}
    neutral: list[Pair] = []
    negative: list[Pair] = []
    for pair, raw in raw_scores.items():
        if pair not in PAIR_UNIVERSE or not math.isfinite(float(raw)):
            raise GDNCorrError("EdgeMask evidence is invalid")
        value = float(raw)
        if value > tolerance:
            positive[pair] = value
        elif value < -tolerance:
            negative.append(pair)
        else:
            neutral.append(pair)
    return SignedEdgeMaskEvidenceR1(
        positive_scores=positive,
        neutral_pairs=tuple(sorted(neutral)),
        counterevidence_pairs=tuple(sorted(negative)),
        tolerance=tolerance,
    )


def corrected_functional_consensus_r1(
    *, raw_edge_mask: Mapping[Pair, float], attention_percentiles: Mapping[Pair, float] | None,
) -> dict[Pair, float]:
    """Build positive functional consensus without attention overriding a nonpositive mask."""

    signed = signed_edgemask_evidence_r1(raw_edge_mask)
    edge_percentiles = observed_percentiles_r1(signed.positive_scores, target_local=True)
    if attention_percentiles is not None and set(attention_percentiles) != set(PAIR_UNIVERSE):
        raise GDNCorrError("attention percentile map must cover the universe")
    result: dict[Pair, float] = {}
    for pair in PAIR_UNIVERSE:
        edge = edge_percentiles[pair]
        if edge <= 0.0:
            result[pair] = 0.0
        elif attention_percentiles is None:
            result[pair] = edge
        else:
            result[pair] = (edge + float(attention_percentiles[pair])) / 2.0
    return result


def matched_random_controls_r1(
    *, focal_edges: Sequence[Pair], eligible_graph_edges: Sequence[Pair],
    seed: int, view: str,
) -> tuple[dict[Pair, Pair], tuple[Pair, ...]]:
    """Assign target-matched controls after excluding the complete focal set.

    Controls are sampled without replacement whenever a target-specific pool
    is large enough.  Focal edges left without an eligible unique control are
    returned explicitly instead of silently weakening the match.
    """

    focal = _pairs(focal_edges)
    eligible = _pairs(eligible_graph_edges)
    if not view or "/" in view or "\\" in view:
        raise GDNCorrError("view must be a symbolic identity")
    if any(edge not in eligible for edge in focal):
        raise GDNCorrError("focal edges must be learned-graph members")
    focal_set = set(focal)
    assignments: dict[Pair, Pair] = {}
    unmatched: list[Pair] = []
    by_target: dict[str, list[Pair]] = {}
    for edge in focal:
        by_target.setdefault(edge[1], []).append(edge)
    for target, target_focal in sorted(by_target.items()):
        candidates = sorted(
            edge for edge in eligible
            if edge[1] == target and edge not in focal_set
        )
        local_seed = int(stable_hash_v1({
            "experiment": "EXP-01B-R1", "seed": int(seed),
            "view": view, "target": target,
            "focal": [list(edge) for edge in sorted(focal_set)],
        })[:16], 16)
        random.Random(local_seed).shuffle(candidates)
        for index, edge in enumerate(sorted(target_focal)):
            if index < len(candidates):
                assignments[edge] = candidates[index]
            else:
                unmatched.append(edge)
    if any(control in focal_set for control in assignments.values()):
        raise GDNCorrError("focal edge leaked into the control set")
    if len(set(assignments.values())) != len(assignments):
        raise GDNCorrError("controls must not be reused when assigned")
    if any(focal[1] != control[1] for focal, control in assignments.items()):
        raise GDNCorrError("control target mismatch")
    return assignments, tuple(sorted(unmatched))


def corrected_meta_stat_scores_r1(
    *, meta_ranking: Sequence[Pair], stat_ranking: Sequence[Pair],
) -> tuple[dict[Pair, float], tuple[Pair, ...]]:
    """Replay the equal-weight META+STAT score and prove the Top-budget union."""

    meta = ranking_membership_percentiles_r1(meta_ranking)
    stat = ranking_membership_percentiles_r1(stat_ranking)
    scores = {pair: (meta[pair] + stat[pair]) / 2.0 for pair in PAIR_UNIVERSE}
    union = tuple(sorted(set(meta_ranking) | set(stat_ranking)))
    ranking = deterministic_ranking_r1(scores)
    if set(ranking[: len(union)]) != set(union):
        raise GDNCorrError("corrected META+STAT Top-budget does not replay the intended union")
    return scores, union


@dataclass(frozen=True)
class PurgedValidationPlanV1:
    validation_blocks: tuple[tuple[int, int, int], ...]
    purge_rows: int
    train_window_indices: tuple[tuple[int, int], ...]
    validation_window_indices: tuple[tuple[int, int], ...]
    raw_timestamp_overlap_count: int


def window_raw_support_v1(*, stop: int, history: int, max_horizon: int) -> range:
    if stop < history or history <= 0 or max_horizon <= 0:
        raise GDNCorrError("window support parameters are invalid")
    return range(stop - history, stop + max_horizon)


def purged_contiguous_validation_plan_v1(
    *, segment_lengths: Sequence[int], seed: int, history: int,
    max_horizon: int, validation_ratio: float,
) -> PurgedValidationPlanV1:
    """Choose one file-local contiguous block and purge all overlapping windows."""

    lengths = tuple(int(value) for value in segment_lengths)
    if not lengths or any(value <= history + max_horizon for value in lengths):
        raise GDNCorrError("segments are too short for multi-horizon windows")
    if not 0.0 < validation_ratio < 0.5:
        raise GDNCorrError("validation ratio is outside the frozen bound")
    per_segment = tuple(value - history - max_horizon + 1 for value in lengths)
    blocks: list[tuple[int, int, int]] = []
    validation_rows: list[tuple[int, int]] = []
    for segment_index, available in enumerate(per_segment):
        validation_count = max(1, int(available * validation_ratio))
        local_seed = int(stable_hash_v1({
            "experiment": "EXP-01C-GDN-HAI-V1", "seed": int(seed),
            "segment_index": segment_index, "segment_length": lengths[segment_index],
            "validation_count": validation_count,
        })[:16], 16)
        start = random.Random(local_seed).randrange(available - validation_count + 1)
        stop = start + validation_count
        blocks.append((segment_index, start, stop))
        validation_rows.extend((segment_index, local) for local in range(start, stop))
    validation = tuple(validation_rows)
    # Every local window ``i`` consumes the closed raw-row interval
    # [i, i + history + max_horizon - 1].  A contiguous validation block can
    # therefore be purged with interval arithmetic.  The former set expansion
    # was mathematically equivalent but expanded tens of millions of tagged
    # row tuples for the real HAI files.
    support_width = history + max_horizon
    block_by_file = {
        file_index: (start, stop - 1 + support_width - 1)
        for file_index, start, stop in blocks
    }
    train: list[tuple[int, int]] = []
    for file_index, count in enumerate(per_segment):
        validation_start, validation_support_stop = block_by_file[file_index]
        for local in range(count):
            local_support_stop = local + support_width - 1
            if local_support_stop < validation_start or local > validation_support_stop:
                train.append((file_index, local))
    return PurgedValidationPlanV1(
        validation_blocks=tuple(blocks),
        purge_rows=history + max_horizon - 1,
        train_window_indices=tuple(train),
        validation_window_indices=validation,
        raw_timestamp_overlap_count=0,
    )


@dataclass(frozen=True)
class FeatureScaleSummaryV1:
    count: int
    finite_count: int
    mean: float
    std: float
    median: float
    iqr: float
    minimum: float
    maximum: float
    median_abs_first_difference: float
    near_zero_variance: bool


def summarize_feature_scales_v1(matrix: Any) -> tuple[FeatureScaleSummaryV1, ...]:
    import numpy as np

    array = np.asarray(matrix, dtype=np.float64)
    if array.ndim != 2 or array.shape[0] < 2:
        raise GDNCorrError("scale audit matrix must be two-dimensional and nonempty")
    summaries: list[FeatureScaleSummaryV1] = []
    for column in array.T:
        finite = column[np.isfinite(column)]
        if finite.size < 2:
            raise GDNCorrError("feature has insufficient finite values")
        q25, median, q75 = np.quantile(finite, (0.25, 0.5, 0.75), method="linear")
        std = float(np.std(finite))
        first = np.diff(finite)
        summaries.append(FeatureScaleSummaryV1(
            count=int(column.size), finite_count=int(finite.size),
            mean=float(np.mean(finite)), std=std, median=float(median),
            iqr=float(q75 - q25), minimum=float(np.min(finite)),
            maximum=float(np.max(finite)),
            median_abs_first_difference=float(np.median(np.abs(first))),
            near_zero_variance=bool(std <= 1e-12 or (q75 - q25) <= 1e-12),
        ))
    return tuple(summaries)


def fit_transform_policy_v1(matrix: Any, *, policy: str) -> tuple[Any, dict[str, Any]]:
    """Fit RAW/standard/robust parameters on one training view only."""

    import numpy as np

    array = np.asarray(matrix, dtype=np.float64)
    if array.ndim != 2 or not bool(np.isfinite(array).all()):
        raise GDNCorrError("training scaler input must be a finite matrix")
    if policy == "RAW_CURRENT":
        center = np.zeros(array.shape[1], dtype=np.float64)
        scale = np.ones(array.shape[1], dtype=np.float64)
    elif policy == "TRAIN_ONLY_STANDARDIZED":
        center = np.mean(array, axis=0)
        scale = np.std(array, axis=0)
    elif policy == "TRAIN_ONLY_ROBUST_MEDIAN_IQR":
        center = np.median(array, axis=0)
        q25, q75 = np.quantile(array, (0.25, 0.75), axis=0, method="linear")
        scale = q75 - q25
    else:
        raise GDNCorrError("unknown preprocessing policy")
    active = scale > 1e-12
    safe_scale = np.where(active, scale, 1.0)
    transformed = (array - center) / safe_scale
    receipt = {
        "policy": policy,
        "feature_count": int(array.shape[1]),
        "near_zero_scale_count": int((~active).sum()),
        "fit_row_count": int(array.shape[0]),
        "fit_scope": "TRAINING_VIEW_ONLY",
        "parameter_hash": stable_hash_v1({
            "policy": policy,
            "center": [float(value).hex() for value in center],
            "scale": [float(value).hex() for value in safe_scale],
            "active": [bool(value) for value in active],
        }),
    }
    return transformed, receipt


def loss_concentration_v1(matrix: Any, *, horizons: Sequence[int] = (1, 5, 10, 30, 60)) -> dict[str, Any]:
    """Measure persistence-baseline squared-error concentration on normal data."""

    import numpy as np

    array = np.asarray(matrix, dtype=np.float64)
    hs = tuple(int(value) for value in horizons)
    if array.ndim != 2 or not hs or any(value <= 0 or value >= array.shape[0] for value in hs):
        raise GDNCorrError("loss concentration input is invalid")
    by_feature = np.zeros(array.shape[1], dtype=np.float64)
    by_horizon: dict[int, list[float]] = {}
    for horizon in hs:
        mse = np.mean((array[horizon:] - array[:-horizon]) ** 2, axis=0)
        by_feature += mse
        by_horizon[horizon] = [float(value) for value in mse]
    total = float(by_feature.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise GDNCorrError("persistence loss concentration is empty")
    ordered = sorted((float(value) for value in by_feature), reverse=True)
    return {
        "top5_share": sum(ordered[:5]) / total,
        "feature_mse_share": [float(value / total) for value in by_feature],
        "horizon_feature_mse": by_horizon,
    }


def aggregate_seed_percentiles_r1(
    values: Mapping[int, Mapping[Pair, float]],
) -> dict[Pair, float]:
    """Median-aggregate exactly seeds 11/23/37 over the complete universe."""

    import statistics

    if set(values) != {11, 23, 37} or any(set(row) != set(PAIR_UNIVERSE) for row in values.values()):
        raise GDNCorrError("seed percentile closure differs from 11/23/37 and 144 pairs")
    return {
        pair: float(statistics.median(float(values[seed][pair]) for seed in (11, 23, 37)))
        for pair in PAIR_UNIVERSE
    }


def augmented_scores_r1(
    *, meta: Mapping[Pair, float], stat: Mapping[Pair, float],
    functional: Mapping[Pair, float],
) -> tuple[dict[Pair, float], dict[Pair, float]]:
    if any(set(item) != set(PAIR_UNIVERSE) for item in (meta, stat, functional)):
        raise GDNCorrError("augmented ranking inputs must cover the pair universe")
    baseline = {pair: (float(meta[pair]) + float(stat[pair])) / 2.0 for pair in PAIR_UNIVERSE}
    augmented = {
        pair: (float(meta[pair]) + float(stat[pair]) + float(functional[pair])) / 3.0
        for pair in PAIR_UNIVERSE
    }
    return baseline, augmented


def jaccard_at_k_r1(left: Sequence[Pair], right: Sequence[Pair], *, k: int) -> float:
    if k <= 0:
        raise GDNCorrError("K must be positive")
    a, b = set(left[:k]), set(right[:k])
    return len(a & b) / len(a | b) if a or b else 1.0


__all__ = [
    "FeatureScaleSummaryV1", "GDNCorrError", "Pair", "PurgedValidationPlanV1",
    "R1_EDGE_TOLERANCE", "SignedEdgeMaskEvidenceR1",
    "aggregate_seed_percentiles_r1", "augmented_scores_r1",
    "corrected_functional_consensus_r1", "corrected_meta_stat_scores_r1",
    "deterministic_ranking_r1", "fit_transform_policy_v1", "loss_concentration_v1",
    "jaccard_at_k_r1", "matched_random_controls_r1", "observed_percentiles_r1",
    "purged_contiguous_validation_plan_v1", "ranking_membership_percentiles_r1",
    "signed_edgemask_evidence_r1", "summarize_feature_scales_v1",
    "window_raw_support_v1",
]
