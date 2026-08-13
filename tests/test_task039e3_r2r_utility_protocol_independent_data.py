from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

from paperworks.data.contracts_v2 import DataViewManifestV2, SplitManifestV2
from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
BASE = "cd6c23b68131820acf03d16cdd78c77db9635f59"
PROTOCOL_A = "0eec09c662ecc1c78daa5f661c2471aba69cf905"
PROTOCOL_B = "c021768fc29a4560bd1bc52f5ed61462731be1c7"


def _document(name: str) -> dict[str, object]:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def _verify(document: dict[str, object]) -> None:
    observed = document["artifact_hash"]
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if observed != stable_hash_v1(payload):
        raise AssertionError("artifact self-hash mismatch")


class IndependentDataAndSplitAuditTests(unittest.TestCase):
    def test_commit_boundaries_are_exact(self) -> None:
        first = subprocess.check_output(
            ["git", "diff", "--name-status", BASE, PROTOCOL_A], cwd=ROOT, text=True
        ).splitlines()
        second = subprocess.check_output(
            ["git", "diff", "--name-status", PROTOCOL_A, PROTOCOL_B], cwd=ROOT, text=True
        ).splitlines()
        self.assertEqual(
            first,
            [
                "A\tsrc/paperworks/v6/task039e3_r2r_utility_protocol_v1.py",
                "A\ttests/test_task039e3_r2r_utility_protocol_v1.py",
            ],
        )
        self.assertEqual(len(second), 16)
        self.assertTrue(all(line.startswith("A\tdocs/task_reports/") for line in second))

    def test_protocol_classification_is_post_result(self) -> None:
        authority = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_AUTHORITY_POLICY.json")
        _verify(authority)
        self.assertEqual(authority["protocol_classification"], "POST_RESULT_PROTOCOL_FREEZE")
        self.assertFalse(authority["precommitted_before_construction_result"])

    def test_dataset_and_utility_view_authorities_self_verify(self) -> None:
        dataset = _document("TASK-039A_DATASET_MANIFEST_V2.json")
        self.assertEqual(
            dataset["artifact_hash"],
            "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2",
        )
        source = DataViewManifestV2.from_dict(
            _document("TASK-039BR2_CANONICAL_RULE_VIEW_V2.json")
        )
        utility = DataViewManifestV2.from_dict(
            _document("TASK-039E3_R2R_UTILITY_PROTOCOL_DATA_VIEW_V2.json")
        )
        self.assertEqual(
            utility.view_id,
            "4445c98c0a22e4f53a5679b39b52a984adf342eb02fe893d5d53256ea2133e24",
        )
        self.assertEqual(source.source_dataset_manifest_id, utility.source_dataset_manifest_id)
        self.assertEqual(source.process_scope, utility.process_scope)
        self.assertEqual(source.sampling_interval_seconds, utility.sampling_interval_seconds)
        self.assertEqual(source.feature_order_hash, utility.feature_order_hash)
        self.assertEqual(dict(source.preprocessing_config), dict(utility.preprocessing_config))
        self.assertFalse(utility.second_level_rule_calibration_allowed)

    def test_split_records_reconstruct_and_sealed_is_absent(self) -> None:
        wrapper = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_SPLIT_MANIFESTS_V2.json")
        _verify(wrapper)
        records = [SplitManifestV2.from_dict(record) for record in wrapper["records"]]
        self.assertEqual(
            [record.split_id for record in records],
            [
                "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0",
                "9d76358ff109e4a6d2a712a1ff679c199d08e9cc92239160c8016e9efa063203",
            ],
        )
        self.assertEqual([(r.raw_ranges[0].start, r.raw_ranges[0].end) for r in records], [(0, 54_000), (54_120, 284_520)])
        self.assertIsNone(wrapper["sealed_evaluation_manifest"])
        self.assertFalse(wrapper["sealed_evaluation_authorized"])

    def test_actual_context_is_smaller_than_purge(self) -> None:
        lookback = 5
        lookahead = max((1, 5, 10, 30, 60)) + 3 - 1
        footprint = lookback + lookahead + 1
        self.assertEqual((lookback, lookahead, footprint), (5, 62, 68))
        self.assertGreater(120, lookback + lookahead)

    def test_logical_physical_mapping_is_not_authority_bound(self) -> None:
        split_policy = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_SPLIT_POLICY.json")
        wrapper = _document("TASK-039E3_R2R_UTILITY_PROTOCOL_SPLIT_MANIFESTS_V2.json")
        joined = json.dumps({"policy": split_policy, "wrapper": wrapper}, sort_keys=True)
        for required_field in (
            "physical_row_mapping",
            "physical_row_index",
            "virtual_non_observation",
            "purge_excluded_from_metric_denominators",
        ):
            self.assertNotIn(required_field, joined)
        outer = wrapper["file_coordinate_map"][1]
        self.assertEqual(outer["logical_range"], {"start": 54_120, "end": 284_520})
        self.assertEqual(outer["observation_count"], 230_400)
        # Identity and reversed file-local orders both satisfy the frozen count/range metadata.
        identity = (0, 230_399)
        reverse = (230_399, 0)
        self.assertNotEqual(identity, reverse)
        self.assertEqual(set(identity), set(reverse))


if __name__ == "__main__":
    unittest.main()
