"""Pure corrected EXP-01B-R1 reanalysis over frozen evidence inputs."""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Mapping, Sequence

from paperworks.validation_v2.exp01_scientific_v1 import PAIR_UNIVERSE
from paperworks.validation_v2.exp01b_contract_v1 import EVALUATION_BUDGETS, PRIMARY_BUDGET, VIEWS
from paperworks.validation_v2.exp01b_ranking_v1 import (
    DispositionEvidenceV1,
    GDNDisposition,
    apply_frozen_disposition_rule_v1,
    directional_relation_yield_at_k_v1,
    precision_recall_ndcg_at_k_v1,
)
from paperworks.validation_v2.gdn_corr_v1 import (
    Pair,
    aggregate_seed_percentiles_r1,
    augmented_scores_r1,
    corrected_functional_consensus_r1,
    corrected_meta_stat_scores_r1,
    deterministic_ranking_r1,
    jaccard_at_k_r1,
    matched_random_controls_r1,
    observed_percentiles_r1,
    ranking_membership_percentiles_r1,
    signed_edgemask_evidence_r1,
)


@dataclass(frozen=True)
class R1EvidenceInputsV1:
    meta_ranking: tuple[Pair, ...]
    stat_ranking: tuple[Pair, ...]
    confirmed_pairs: frozenset[Pair]
    confirmed_directional_pairs: tuple[Pair, ...]
    embedding: Mapping[tuple[str, int], Mapping[Pair, float]]
    attention: Mapping[tuple[str, int], Mapping[Pair, float]]
    edge_mask: Mapping[tuple[str, int], Mapping[Pair, float]]
    graph_edges: Mapping[tuple[str, int], tuple[Pair, ...]]


@dataclass(frozen=True)
class R1AnalysisV1:
    metric_rows: tuple[dict[str, object], ...]
    stability_rows: tuple[dict[str, object], ...]
    random_rows: tuple[dict[str, object], ...]
    baseline_ranking: tuple[Pair, ...]
    augmented_ranking: tuple[Pair, ...]
    gdn_unique_confirmed_pairs: tuple[Pair, ...]
    disposition: GDNDisposition
    disposition_evidence: DispositionEvidenceV1
    signed_counts: Mapping[str, int]


def _validate(inputs: R1EvidenceInputsV1) -> None:
    expected = {(view, seed) for view in VIEWS for seed in (11, 23, 37)}
    for name, values in (
        ("embedding", inputs.embedding), ("attention", inputs.attention),
        ("edge_mask", inputs.edge_mask), ("graph_edges", inputs.graph_edges),
    ):
        if set(values) != expected:
            raise ValueError(f"EXP01B_R1_{name.upper()}_RUN_CLOSURE_MISMATCH")
    if any(pair not in PAIR_UNIVERSE for pair in inputs.confirmed_pairs):
        raise ValueError("EXP01B_R1_REFERENCE_PAIR_INVALID")


def analyze_exp01b_r1_v1(
    inputs: R1EvidenceInputsV1, *, unique_executable_rule_pair_count: int,
) -> R1AnalysisV1:
    _validate(inputs)
    meta, union = corrected_meta_stat_scores_r1(
        meta_ranking=inputs.meta_ranking, stat_ranking=inputs.stat_ranking,
    )
    meta_membership = ranking_membership_percentiles_r1(inputs.meta_ranking)
    stat_membership = ranking_membership_percentiles_r1(inputs.stat_ranking)
    functional: dict[str, dict[Pair, float]] = {}
    seed_rankings: dict[tuple[str, int], tuple[Pair, ...]] = {}
    signed_counts = {"positive": 0, "neutral": 0, "counterevidence": 0}
    for view in VIEWS:
        by_seed: dict[int, Mapping[Pair, float]] = {}
        for seed in (11, 23, 37):
            key = (view, seed)
            signed = signed_edgemask_evidence_r1(inputs.edge_mask[key])
            signed_counts["positive"] += len(signed.positive_scores)
            signed_counts["neutral"] += len(signed.neutral_pairs)
            signed_counts["counterevidence"] += len(signed.counterevidence_pairs)
            attention = observed_percentiles_r1(inputs.attention[key], target_local=True)
            consensus = corrected_functional_consensus_r1(
                raw_edge_mask=inputs.edge_mask[key], attention_percentiles=attention,
            )
            by_seed[seed] = consensus
            seed_rankings[(view, seed)] = deterministic_ranking_r1(consensus)
        functional[view] = aggregate_seed_percentiles_r1(by_seed)

    baseline_scores, augmented_combined = augmented_scores_r1(
        meta=meta_membership, stat=stat_membership,
        functional=functional["TRAIN1_TRAIN2_COMBINED"],
    )
    if baseline_scores != meta:
        raise ValueError("EXP01B_R1_META_STAT_REPLAY_MISMATCH")
    baseline_ranking = deterministic_ranking_r1(baseline_scores)
    if set(baseline_ranking[:len(union)]) != set(union):
        raise ValueError("EXP01B_R1_META_STAT_UNION_NOT_REPLAYED")
    augmented_by_view: dict[str, tuple[Pair, ...]] = {}
    for view in VIEWS:
        _, scores = augmented_scores_r1(
            meta=meta_membership, stat=stat_membership, functional=functional[view],
        )
        augmented_by_view[view] = deterministic_ranking_r1(scores)
    augmented_ranking = deterministic_ranking_r1(augmented_combined)

    metric_rows: list[dict[str, object]] = []
    for arm, ranking in (("META_STAT", baseline_ranking), ("META_STAT_GDN_CORRECTED", augmented_ranking)):
        for k in EVALUATION_BUDGETS:
            metrics = precision_recall_ndcg_at_k_v1(
                ranking, confirmed_pairs=inputs.confirmed_pairs, k=k,
            )
            metric_rows.append({
                "arm": arm, "k": k, **metrics,
                "confirmed_directional_relation_yield": directional_relation_yield_at_k_v1(
                    ranking, directional_relation_pairs=inputs.confirmed_directional_pairs, k=k,
                ),
            })

    stability_rows: list[dict[str, object]] = []
    for view in VIEWS:
        for k in EVALUATION_BUDGETS:
            rankings = {seed: seed_rankings[(view, seed)] for seed in (11, 23, 37)}
            seed_jaccard = statistics.mean(
                jaccard_at_k_r1(rankings[left], rankings[right], k=k)
                for left, right in ((11, 23), (11, 37), (23, 37))
            )
            stability_rows.append({"view": view, "k": k, "seed_jaccard_mean": seed_jaccard})

    random_rows: list[dict[str, object]] = []
    matched_passes = 0
    positive_medians: list[float] = []
    for seed in (11, 23, 37):
        key = ("TRAIN1_TRAIN2_COMBINED", seed)
        signed = signed_edgemask_evidence_r1(inputs.edge_mask[key])
        positive_ranking = deterministic_ranking_r1(
            observed_percentiles_r1(signed.positive_scores, target_local=True),
        )
        focal = tuple(pair for pair in positive_ranking if pair in signed.positive_scores)[:PRIMARY_BUDGET]
        assignments, unmatched = matched_random_controls_r1(
            focal_edges=focal, eligible_graph_edges=inputs.graph_edges[key], seed=seed,
            view="TRAIN1_TRAIN2_COMBINED",
        )
        comparable = tuple(
            (focal_pair, control_pair) for focal_pair, control_pair in assignments.items()
            if control_pair in inputs.edge_mask[key]
        )
        focal_values = [inputs.edge_mask[key][left] for left, _ in comparable]
        control_values = [inputs.edge_mask[key][right] for _, right in comparable]
        passed = bool(focal_values) and statistics.median(focal_values) > statistics.median(control_values)
        matched_passes += int(passed)
        if focal_values:
            positive_medians.append(statistics.median(focal_values))
        random_rows.append({
            "view": "TRAIN1_TRAIN2_COMBINED", "seed": seed,
            "focal_count": len(focal), "matched_count": len(comparable),
            "unmatched_count": len(unmatched) + len(assignments) - len(comparable),
            "focal_median_positive": bool(focal_values and statistics.median(focal_values) > 0),
            "focal_exceeds_control": passed,
        })

    unique_confirmed = tuple(sorted(
        pair for pair in set(augmented_ranking[:PRIMARY_BUDGET]) - set(union)
        if pair in inputs.confirmed_pairs
    ))
    stable_unique = sum(
        sum(inputs.edge_mask[("TRAIN1_TRAIN2_COMBINED", seed)].get(pair, 0.0) > 1e-12 for seed in (11, 23, 37)) >= 2
        for pair in unique_confirmed
    )
    stable_meta = sum(
        sum(inputs.edge_mask[("TRAIN1_TRAIN2_COMBINED", seed)].get(pair, 0.0) > 1e-12 for seed in (11, 23, 37)) >= 2
        for pair in union
    )
    lookup = {(row["arm"], row["k"]): row for row in metric_rows}
    base = lookup[("META_STAT", PRIMARY_BUDGET)]
    aug = lookup[("META_STAT_GDN_CORRECTED", PRIMARY_BUDGET)]
    view_metrics = {}
    for view in ("TRAIN1_ONLY", "TRAIN2_ONLY"):
        view_metrics[view] = precision_recall_ndcg_at_k_v1(
            augmented_by_view[view], confirmed_pairs=inputs.confirmed_pairs, k=PRIMARY_BUDGET,
        )
    evidence = DispositionEvidenceV1(
        augmented_confirmed_yield=int(aug["confirmed_pair_yield"]),
        baseline_confirmed_yield=int(base["confirmed_pair_yield"]),
        augmented_ndcg=float(aug["ndcg"]), baseline_ndcg=float(base["ndcg"]),
        train1_yield_non_degraded=int(view_metrics["TRAIN1_ONLY"]["confirmed_pair_yield"]) >= int(base["confirmed_pair_yield"]),
        train2_yield_non_degraded=int(view_metrics["TRAIN2_ONLY"]["confirmed_pair_yield"]) >= int(base["confirmed_pair_yield"]),
        train1_ndcg_non_degraded=float(view_metrics["TRAIN1_ONLY"]["ndcg"]) >= float(base["ndcg"]),
        train2_ndcg_non_degraded=float(view_metrics["TRAIN2_ONLY"]["ndcg"]) >= float(base["ndcg"]),
        gdn_unique_confirmed_pairs=len(unique_confirmed),
        gdn_unique_executable_rule_pairs=int(unique_executable_rule_pair_count),
        positive_median_top_edge_mask=bool(positive_medians and statistics.median(positive_medians) > 0),
        combined_seeds_edge_mask_exceeds_random=matched_passes,
        stable_unique_positive_pairs_two_seeds=stable_unique,
        stable_meta_stat_functional_pairs_two_seeds=stable_meta,
    )
    return R1AnalysisV1(
        metric_rows=tuple(metric_rows), stability_rows=tuple(stability_rows),
        random_rows=tuple(random_rows), baseline_ranking=baseline_ranking,
        augmented_ranking=augmented_ranking,
        gdn_unique_confirmed_pairs=unique_confirmed,
        disposition=apply_frozen_disposition_rule_v1(evidence),
        disposition_evidence=evidence, signed_counts=signed_counts,
    )


__all__ = ["R1AnalysisV1", "R1EvidenceInputsV1", "analyze_exp01b_r1_v1"]
