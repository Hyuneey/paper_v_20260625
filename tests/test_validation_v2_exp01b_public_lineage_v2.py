from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import statistics
import unittest

from paperworks.validation_v2.exp01b_ranking_v1 import (
    directional_relation_yield_at_k_v1,
    jaccard_at_k_v1,
    precision_recall_ndcg_at_k_v1,
)
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "research_control_center/validation_v2/exp01b_gdn_xai"
RESULTS = PUBLIC / "results"
RECEIPTS = PUBLIC / "receipts"


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise AssertionError(path)
    return value


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _self_hash(document: dict[str, object], field: str) -> str:
    body = {key: value for key, value in document.items() if key != field}
    return stable_hash_v1(body)


def _pairs(rows: list[dict[str, str]]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (row["source"], row["target"])
        for row in sorted(rows, key=lambda item: int(item["rank"]))
    )


class Exp01BPublicLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = _json(RESULTS / "EXP01B_PUBLIC_RESULT_FREEZE_V2.json")
        cls.reference = _json(RECEIPTS / "EXP01B_REFERENCE_SET_RECEIPT.json")
        cls.original = _json(RESULTS / "EXP01B_DISPOSITION.json")

    def test_all_json_hashes_and_cross_file_hashes_replay(self) -> None:
        self.assertEqual(self.freeze["freeze_hash"], _self_hash(self.freeze, "freeze_hash"))
        for path in sorted(PUBLIC.rglob("*.json")):
            document = _json(path)
            field = "freeze_hash" if "freeze_hash" in document else (
                "result_hash" if "result_hash" in document else "receipt_hash"
            )
            if field in document:
                self.assertEqual(document[field], _self_hash(document, field), path.name)
        for name, expected in self.freeze["original_file_sha256"].items():
            self.assertEqual(_file_hash(RESULTS / name), expected, name)
        for name, expected in self.freeze["lineage_table_sha256"].items():
            self.assertEqual(_file_hash(RESULTS / name), expected, name)
        receipt_files = {
            "reference": "EXP01B_REFERENCE_SET_RECEIPT.json",
            "attention": "EXP01B_ATTENTION_CAPTURE_RECEIPT.json",
            "edgemask": "EXP01B_EDGEMASK_RECEIPT.json",
            "occlusion": "EXP01B_OCCLUSION_RECEIPT.json",
            "lineage_cache": "EXP01B_LINEAGE_CACHE_RECEIPT.json",
            "lineage_input": "EXP01B_LINEAGE_CLOSURE_INPUT_ATTEMPT_003.json",
        }
        for key, name in receipt_files.items():
            self.assertEqual(
                _json(RECEIPTS / name)["receipt_hash"],
                self.freeze["lineage_receipt_hashes"][key],
            )

    def test_all_arm_metrics_replay_from_public_pair_identities(self) -> None:
        ranking_rows = _csv(RESULTS / "EXP01B_ARM_PAIR_RANKINGS.csv")
        groups: dict[tuple[str, str], list[dict[str, str]]] = {}
        for row in ranking_rows:
            groups.setdefault((row["arm"], row["view"]), []).append(row)
        self.assertEqual(len(ranking_rows), 2736)
        self.assertEqual(len(groups), 19)
        self.assertTrue(all(len(rows) == 144 for rows in groups.values()))
        self.assertTrue(all(len(set(_pairs(rows))) == 144 for rows in groups.values()))

        confirmed = frozenset(
            (str(row["source"]), str(row["target"]))
            for row in self.reference["confirmed_pairs"]
        )
        directional = tuple(
            (str(row["source"]), str(row["target"]))
            for row in self.reference["confirmed_directional_relations"]
        )
        metrics = _csv(RESULTS / "EXP01B_ARM_METRICS.csv")
        self.assertEqual(len(metrics), 76)
        for row in metrics:
            ranking = _pairs(groups[(row["arm"], row["view"])])
            k = int(row["k"])
            replay = precision_recall_ndcg_at_k_v1(
                ranking, confirmed_pairs=confirmed, k=k,
            )
            replay["confirmed_directional_relation_yield"] = (
                directional_relation_yield_at_k_v1(
                    ranking, directional_relation_pairs=directional, k=k,
                )
            )
            for field in ("confirmed_pair_yield", "confirmed_directional_relation_yield"):
                self.assertEqual(int(row[field]), int(replay[field]))
            for field in ("precision", "recall", "ndcg"):
                self.assertAlmostEqual(float(row[field]), float(replay[field]), places=12)

        old = _csv(RESULTS / "EXP01B_RANKING_RESULTS.csv")
        lookup = {
            (row["arm"], int(row["k"])): row
            for row in metrics if row["view"] == "GLOBAL"
        }
        for row in old:
            replay = lookup[(row["arm"], int(row["k"]))]
            for field in row:
                if field not in {"arm", "k"}:
                    self.assertAlmostEqual(float(row[field]), float(replay[field]), places=12)

    def test_seed_and_split_stability_replays(self) -> None:
        aggregate_rows = _csv(RESULTS / "EXP01B_ARM_PAIR_RANKINGS.csv")
        aggregate_groups: dict[tuple[str, str], list[dict[str, str]]] = {}
        for row in aggregate_rows:
            aggregate_groups.setdefault((row["arm"], row["view"]), []).append(row)
        seed_rows = _csv(RESULTS / "EXP01B_ARM_SEED_RANKINGS.csv")
        seed_groups: dict[tuple[str, str, int], list[dict[str, str]]] = {}
        for row in seed_rows:
            seed_groups.setdefault((row["arm"], row["view"], int(row["seed"])), []).append(row)
        self.assertEqual(len(seed_rows), 6480)
        self.assertEqual(len(seed_groups), 45)
        self.assertTrue(all(len(rows) == 144 for rows in seed_groups.values()))

        for row in _csv(RESULTS / "EXP01B_ARM_STABILITY.csv"):
            arm, k = row["arm"], int(row["k"])
            per_view = {
                view: {seed: _pairs(seed_groups[(arm, view, seed)]) for seed in (11, 23, 37)}
                for view in ("TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY")
            }
            def mean_jaccard(view: str) -> float:
                ranks = per_view[view]
                return statistics.mean(
                    jaccard_at_k_v1(ranks[left], ranks[right], k=k)
                    for left, right in ((11, 23), (11, 37), (23, 37))
                )
            self.assertAlmostEqual(float(row["combined_seed_jaccard_mean"]), mean_jaccard("TRAIN1_TRAIN2_COMBINED"), places=12)
            self.assertAlmostEqual(float(row["train1_seed_jaccard_mean"]), mean_jaccard("TRAIN1_ONLY"), places=12)
            self.assertAlmostEqual(float(row["train2_seed_jaccard_mean"]), mean_jaccard("TRAIN2_ONLY"), places=12)
            split_aggregate = jaccard_at_k_v1(
                _pairs(aggregate_groups[(arm, "TRAIN1_ONLY")]),
                _pairs(aggregate_groups[(arm, "TRAIN2_ONLY")]), k=k,
            )
            split_seed = statistics.mean(
                jaccard_at_k_v1(
                    per_view["TRAIN1_ONLY"][seed], per_view["TRAIN2_ONLY"][seed], k=k,
                )
                for seed in (11, 23, 37)
            )
            self.assertAlmostEqual(float(row["split_jaccard_aggregate"]), split_aggregate, places=12)
            self.assertAlmostEqual(float(row["split_jaccard_seed_mean"]), split_seed, places=12)

    def test_matched_controls_and_frozen_disposition_remain_exact(self) -> None:
        rows = _csv(RESULTS / "EXP01B_MATCHED_RANDOM_CONTROLS.csv")
        counts: dict[str, int] = {}
        passes = 0
        for seed in (11, 23, 37):
            selected = [row for row in rows if int(row["seed"]) == seed]
            counts[str(seed)] = len(selected)
            if selected and statistics.median(float(row["focal_relative_delta_mse"]) for row in selected) > statistics.median(
                float(row["control_relative_delta_mse"]) for row in selected
            ):
                passes += 1
        self.assertEqual(counts, {str(key): int(value) for key, value in self.original["matched_random_comparison_counts"].items()})
        self.assertEqual(passes, int(self.original["edge_mask_exceeds_matched_random_combined_seed_count"]))
        self.assertEqual(self.original["disposition"], "GDN_ABLATION_ONLY")
        self.assertEqual(self.freeze["disposition"], self.original["disposition"])
        self.assertFalse(self.freeze["disposition_changed"])
        self.assertEqual(self.freeze["original_result_hash"], self.original["result_hash"])

        conversion = _csv(RESULTS / "EXP01B_RULE_CONVERSION_RESULTS.csv")
        self.assertEqual(sum(row["normal_confirmed"] == "True" for row in conversion), 37)
        self.assertEqual(sum(row["formal_v4_executable"] == "True" for row in conversion), 21)
        self.assertEqual(sum(row["gdn_unique_at_primary_budget"] == "True" and row["formal_v4_executable"] == "True" for row in conversion), 0)

    def test_access_counters_and_public_privacy_are_closed(self) -> None:
        for path in sorted(PUBLIC.rglob("*.json")):
            document = _json(path)
            serialized = json.dumps(document, sort_keys=True)
            self.assertNotRegex(serialized, re.compile(r"(?i)[a-z]:[\\/]"), path.name)
            self.assertNotIn("Desktop\\paperworks", serialized)
            for key in ("test1_accesses", "label_accesses", "test2_accesses", "heldout_accesses", "provider_calls"):
                if key in document:
                    self.assertEqual(document[key], 0, f"{path.name}:{key}")
        for path in sorted(PUBLIC.rglob("*")):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, re.compile(r"(?i)(api[_-]?key|signed[_-]?url|credential)\s*[:=]"), path.name)
        cache = _json(RECEIPTS / "EXP01B_LINEAGE_CACHE_RECEIPT.json")
        self.assertEqual(cache["cache_count"], 9)
        self.assertFalse(cache["private_cache_committed"])
        self.assertFalse(cache["private_paths_disclosed"])
        self.assertFalse(self.freeze["training_reexecuted"])
        self.assertFalse(self.freeze["hyperparameters_changed"])
        self.assertFalse(self.freeze["selection_rule_changed"])


if __name__ == "__main__":
    unittest.main()
