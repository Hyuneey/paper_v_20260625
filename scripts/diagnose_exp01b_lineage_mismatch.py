#!/usr/bin/env python3
"""Report only sanitized EXP-01B replay deltas from completed private caches."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import finalize_exp01b_public_lineage as closure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    root = parser.parse_args().repository_root.resolve(strict=True)
    meta, stat, _ = closure.original._load_rankings_and_conversion(root)
    reference = closure._load_json(
        root / closure.RECEIPT_ROOT / "EXP01B_REFERENCE_SET_RECEIPT.json"
    )
    confirmed = frozenset(
        (str(row["source"]), str(row["target"]))
        for row in reference["confirmed_pairs"]
    )
    directional = tuple(
        (str(row["source"]), str(row["target"]))
        for row in reference["confirmed_directional_relations"]
    )
    functional = closure._read_functional_rows(
        root / closure.RESULT_ROOT / "EXP01B_FUNCTIONAL_RESULTS.csv"
    )
    edge_by_seed: dict[int, dict[tuple[str, str], float]] = {}
    attention_by_seed: dict[int, dict[tuple[str, str], float]] = {}
    for view in closure.VIEWS:
        for seed in (11, 23, 37):
            run_id = f"exp01b-{view.lower().replace('_', '-')}-seed-{seed}"
            path = root / closure.PRIVATE_LINEAGE_CACHE / f"{run_id}.json"
            document = closure._load_json(path)
            record = closure._load_private_cache(
                path, expected_identity=document["identity"],
            )
            assert record is not None
            edge = closure.target_local_percentiles_v1(
                functional[("GDN_EDGEMASK", view, seed)]
            )
            attention = closure.target_local_percentiles_v1(record.attention_scores)
            if view == "TRAIN1_TRAIN2_COMBINED":
                edge_by_seed[seed] = edge
                attention_by_seed[seed] = attention
    combined = closure._aggregate_functional_consensus(
        edge_by_seed=edge_by_seed, attention_by_seed=attention_by_seed,
    )
    meta_scores = closure.ranking_membership_percentiles_v1(meta)
    stat_scores = closure.ranking_membership_percentiles_v1(stat)
    baseline_scores, augmented_scores = closure.equal_weight_augmented_scores_v1(
        meta=meta_scores, stat=stat_scores, gdn_functional_consensus=combined,
    )
    rankings = {
        "META_STAT": closure.deterministic_ranking_v1(baseline_scores),
        "META_STAT_GDN_AUGMENTED": closure.deterministic_ranking_v1(augmented_scores),
    }
    observed: dict[tuple[str, int], dict[str, object]] = {}
    for arm, ranking in rankings.items():
        for k in closure.EVALUATION_BUDGETS:
            observed[(arm, k)] = {
                **closure.precision_recall_ndcg_at_k_v1(
                    ranking, confirmed_pairs=confirmed, k=k,
                ),
                "confirmed_directional_relation_yield": (
                    closure.directional_relation_yield_at_k_v1(
                        ranking, directional_relation_pairs=directional, k=k,
                    )
                ),
            }
    mismatches: list[dict[str, object]] = []
    with (root / closure.RESULT_ROOT / "EXP01B_RANKING_RESULTS.csv").open(
        "r", encoding="utf-8", newline="",
    ) as stream:
        for row in csv.DictReader(stream):
            arm, k = str(row["arm"]), int(row["k"])
            actual = observed[(arm, k)]
            for field in (
                "confirmed_pair_yield", "confirmed_directional_relation_yield",
                "precision", "recall", "ndcg",
            ):
                expected = float(row[field])
                value = float(actual[field])
                if abs(expected - value) > 1e-12:
                    mismatches.append({
                        "arm": arm, "k": k, "field": field,
                        "frozen": expected, "replay": value,
                    })
    print(json.dumps({
        "status": "MATCH" if not mismatches else "MISMATCH",
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "heldout_accesses": 0,
        "private_values_printed": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
