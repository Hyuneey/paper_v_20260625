"""Deterministic ranking, equal-budget metrics, and GDN disposition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import statistics
from typing import Iterable, Mapping, Sequence

from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE


class Exp01BRankingError(ValueError):
    """Fail-closed EXP-01B ranking error."""


Pair = tuple[str, str]


class GDNDisposition(str, Enum):
    PRIMARY_AUGMENTATION = "GDN_PRIMARY_AUGMENTATION"
    SUPPORTING_EVIDENCE = "GDN_SUPPORTING_EVIDENCE"
    ABLATION_ONLY = "GDN_ABLATION_ONLY"


def _validate_score_map(scores: Mapping[Pair, float]) -> None:
    if any(pair not in PAIR_UNIVERSE for pair in scores):
        raise Exp01BRankingError("score map exceeds frozen 144-pair universe")
    if any(not math.isfinite(float(value)) for value in scores.values()):
        raise Exp01BRankingError("rank scores must be finite")


def target_local_percentiles_v1(scores: Mapping[Pair, float]) -> dict[Pair, float]:
    """Rank observed evidence target-locally; absent edges get no evidence."""

    _validate_score_map(scores)
    result = {pair: 0.0 for pair in PAIR_UNIVERSE}
    by_target: dict[str, list[tuple[Pair, float]]] = {}
    for pair, score in scores.items():
        by_target.setdefault(pair[1], []).append((pair, float(score)))
    for rows in by_target.values():
        ordered = sorted(rows, key=lambda row: (-row[1], row[0]))
        count = len(ordered)
        for rank, (pair, _) in enumerate(ordered):
            result[pair] = 1.0 if count == 1 else 1.0 - rank / (count - 1)
    return result


def aggregate_seed_percentiles_v1(
    percentiles_by_seed: Mapping[int, Mapping[Pair, float]],
) -> dict[Pair, float]:
    if set(percentiles_by_seed) != {11, 23, 37}:
        raise Exp01BRankingError("exact seeds 11/23/37 required")
    for values in percentiles_by_seed.values():
        if set(values) != set(PAIR_UNIVERSE):
            raise Exp01BRankingError("each seed percentile map must cover the full universe")
    return {
        pair: float(statistics.median(percentiles_by_seed[seed][pair] for seed in (11, 23, 37)))
        for pair in PAIR_UNIVERSE
    }


def deterministic_ranking_v1(percentiles: Mapping[Pair, float]) -> tuple[Pair, ...]:
    if set(percentiles) != set(PAIR_UNIVERSE):
        raise Exp01BRankingError("ranking must cover the complete pair universe")
    _validate_score_map(percentiles)
    return tuple(sorted(PAIR_UNIVERSE, key=lambda pair: (-float(percentiles[pair]), pair)))


def functional_consensus_v1(
    *, edge_mask: Mapping[Pair, float], attention: Mapping[Pair, float] | None,
) -> dict[Pair, float]:
    if set(edge_mask) != set(PAIR_UNIVERSE):
        raise Exp01BRankingError("EdgeMask percentile map must cover the universe")
    if attention is None:
        return dict(edge_mask)
    if set(attention) != set(PAIR_UNIVERSE):
        raise Exp01BRankingError("attention percentile map must cover the universe")
    return {pair: (float(edge_mask[pair]) + float(attention[pair])) / 2.0 for pair in PAIR_UNIVERSE}


def equal_weight_augmented_scores_v1(
    *, meta: Mapping[Pair, float], stat: Mapping[Pair, float],
    gdn_functional_consensus: Mapping[Pair, float],
) -> tuple[dict[Pair, float], dict[Pair, float]]:
    if any(set(values) != set(PAIR_UNIVERSE) for values in (meta, stat, gdn_functional_consensus)):
        raise Exp01BRankingError("augmented score inputs must cover the pair universe")
    meta_stat = {pair: (float(meta[pair]) + float(stat[pair])) / 2.0 for pair in PAIR_UNIVERSE}
    augmented = {
        pair: (float(meta[pair]) + float(stat[pair]) + float(gdn_functional_consensus[pair])) / 3.0
        for pair in PAIR_UNIVERSE
    }
    return meta_stat, augmented


def precision_recall_ndcg_at_k_v1(
    ranking: Sequence[Pair], *, confirmed_pairs: Iterable[Pair], k: int,
) -> dict[str, float | int]:
    ordered = tuple(ranking)
    if len(ordered) != len(set(ordered)) or any(pair not in PAIR_UNIVERSE for pair in ordered):
        raise Exp01BRankingError("ranking identities are invalid")
    if k <= 0 or k > len(ordered):
        raise Exp01BRankingError("evaluation budget is invalid")
    relevant = frozenset(confirmed_pairs)
    if not relevant or any(pair not in PAIR_UNIVERSE for pair in relevant):
        raise Exp01BRankingError("normal-confirmed pair reference must be non-empty and in scope")
    top = ordered[:k]
    hits = sum(pair in relevant for pair in top)
    dcg = sum((1.0 / math.log2(rank + 2)) for rank, pair in enumerate(top) if pair in relevant)
    ideal_hits = min(k, len(relevant))
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_hits))
    return {
        "k": k,
        "confirmed_pair_yield": hits,
        "precision": hits / k,
        "recall": hits / len(relevant),
        "ndcg": dcg / idcg,
    }


def directional_relation_yield_at_k_v1(
    ranking: Sequence[Pair], *, directional_relation_pairs: Sequence[Pair], k: int,
) -> int:
    if k <= 0 or k > len(ranking):
        raise Exp01BRankingError("directional-yield budget is invalid")
    if any(pair not in PAIR_UNIVERSE for pair in directional_relation_pairs):
        raise Exp01BRankingError("directional relation lies outside the pair universe")
    return sum(pair in set(ranking[:k]) for pair in directional_relation_pairs)


def jaccard_at_k_v1(left: Sequence[Pair], right: Sequence[Pair], *, k: int) -> float:
    left_set, right_set = set(left[:k]), set(right[:k])
    union = left_set | right_set
    if len(left_set) != k or len(right_set) != k or not union:
        raise Exp01BRankingError("Jaccard inputs must provide exact Top-K sets")
    return len(left_set & right_set) / len(union)


@dataclass(frozen=True)
class DispositionEvidenceV1:
    augmented_confirmed_yield: int
    baseline_confirmed_yield: int
    augmented_ndcg: float
    baseline_ndcg: float
    train1_yield_non_degraded: bool
    train2_yield_non_degraded: bool
    train1_ndcg_non_degraded: bool
    train2_ndcg_non_degraded: bool
    gdn_unique_confirmed_pairs: int
    gdn_unique_executable_rule_pairs: int
    positive_median_top_edge_mask: bool
    combined_seeds_edge_mask_exceeds_random: int
    stable_unique_positive_pairs_two_seeds: int
    stable_meta_stat_functional_pairs_two_seeds: int

    def __post_init__(self) -> None:
        numeric = (
            self.augmented_ndcg, self.baseline_ndcg,
        )
        if any(not math.isfinite(value) or value < 0 or value > 1 for value in numeric):
            raise Exp01BRankingError("NDCG values must lie in [0,1]")
        counts = (
            self.augmented_confirmed_yield, self.baseline_confirmed_yield,
            self.gdn_unique_confirmed_pairs, self.gdn_unique_executable_rule_pairs,
            self.combined_seeds_edge_mask_exceeds_random,
            self.stable_unique_positive_pairs_two_seeds,
            self.stable_meta_stat_functional_pairs_two_seeds,
        )
        if any(type(value) is not int or value < 0 for value in counts):
            raise Exp01BRankingError("disposition counts must be nonnegative integers")
        if self.combined_seeds_edge_mask_exceeds_random > 3:
            raise Exp01BRankingError("only three combined-view seeds exist")


def apply_frozen_disposition_rule_v1(evidence: DispositionEvidenceV1) -> GDNDisposition:
    yield_improved = evidence.augmented_confirmed_yield > evidence.baseline_confirmed_yield
    ndcg_improved = evidence.augmented_ndcg > evidence.baseline_ndcg
    yield_not_worse = evidence.augmented_confirmed_yield >= evidence.baseline_confirmed_yield
    ndcg_not_worse = evidence.augmented_ndcg >= evidence.baseline_ndcg
    primary = (
        (yield_improved or ndcg_improved)
        and ((yield_improved and ndcg_not_worse) or (ndcg_improved and yield_not_worse))
        and evidence.train1_yield_non_degraded
        and evidence.train2_yield_non_degraded
        and evidence.train1_ndcg_non_degraded
        and evidence.train2_ndcg_non_degraded
        and evidence.gdn_unique_confirmed_pairs >= 1
        and evidence.gdn_unique_executable_rule_pairs >= 1
        and evidence.positive_median_top_edge_mask
        and evidence.combined_seeds_edge_mask_exceeds_random >= 2
    )
    if primary:
        return GDNDisposition.PRIMARY_AUGMENTATION
    supporting_a = evidence.stable_unique_positive_pairs_two_seeds >= 1
    supporting_b = (
        evidence.augmented_confirmed_yield == evidence.baseline_confirmed_yield
        and ndcg_improved
        and evidence.train1_yield_non_degraded
        and evidence.train2_yield_non_degraded
        and evidence.train1_ndcg_non_degraded
        and evidence.train2_ndcg_non_degraded
    )
    supporting_c = (
        evidence.stable_meta_stat_functional_pairs_two_seeds >= 1
        and evidence.combined_seeds_edge_mask_exceeds_random >= 2
    )
    if supporting_a or supporting_b or supporting_c:
        return GDNDisposition.SUPPORTING_EVIDENCE
    return GDNDisposition.ABLATION_ONLY


__all__ = [
    "DispositionEvidenceV1", "Exp01BRankingError", "GDNDisposition",
    "aggregate_seed_percentiles_v1", "apply_frozen_disposition_rule_v1",
    "deterministic_ranking_v1", "directional_relation_yield_at_k_v1", "equal_weight_augmented_scores_v1",
    "functional_consensus_v1", "jaccard_at_k_v1",
    "precision_recall_ndcg_at_k_v1", "target_local_percentiles_v1",
]
