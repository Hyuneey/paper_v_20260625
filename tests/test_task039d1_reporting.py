from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.profiling.task039d1_fit_v1 import (
    ARTIFACT_CLASS_BY_TYPE,
    STATUS,
    verify_d1_self_hash_v1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/task_reports"
RESULTS = (
    "TASK-039D1_DATA_ACCESS_AUDIT.json",
    "TASK-039D1_PAIR_FIT_SUMMARY.json",
    "TASK-039D1_FIT_RESULT.json",
    "TASK-039D1_ARM_FIT_SUMMARY.json",
    "TASK-039D1_EXECUTION_RECEIPT.json",
)


class Task039D1ReportingTests(unittest.TestCase):
    def _documents(self) -> list[dict]:
        if not all((REPORTS / name).is_file() for name in RESULTS):
            self.skipTest("D1 result artifacts are created only after clean Commit A execution")
        return [json.loads((REPORTS / name).read_text(encoding="utf-8")) for name in RESULTS]

    def test_result_instances_self_hash_and_schema_validate(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        for document in self._documents():
            verify_d1_self_hash_v1(document)
            ARTIFACT_CLASS_BY_TYPE[document["artifact_type"]].from_dict(document)
            self.assertEqual(
                list(Draft202012Validator(registry.schema_for(document["artifact_type"])).iter_errors(document)),
                [],
            )

    def test_result_counts_and_pair_aggregation(self) -> None:
        self._documents()
        fit = json.loads((REPORTS / "TASK-039D1_FIT_RESULT.json").read_text(encoding="utf-8"))
        pair = json.loads((REPORTS / "TASK-039D1_PAIR_FIT_SUMMARY.json").read_text(encoding="utf-8"))
        self.assertEqual(fit["status"], STATUS)
        self.assertEqual(len(pair["pair_outcomes"]), 47)
        self.assertEqual(fit["directional_opportunity_count"], 94)
        self.assertEqual(fit["pair_fit_supported_count"] + fit["pair_fit_unsupported_count"], 47)
        self.assertEqual(
            fit["directional_fit_supported_count"] + fit["direction_unstable_count"] + fit["fit_unsupported_directional_count"],
            94,
        )
        for item in pair["pair_outcomes"]:
            expected = "fit_supported_pair" if "fit_supported" in {item["step_up_status"], item["step_down_status"]} else "fit_unsupported_pair"
            self.assertEqual(item["pair_fit_status"], expected)

    def test_access_and_authority_boundaries(self) -> None:
        self._documents()
        access = json.loads((REPORTS / "TASK-039D1_DATA_ACCESS_AUDIT.json").read_text(encoding="utf-8"))
        fit = json.loads((REPORTS / "TASK-039D1_FIT_RESULT.json").read_text(encoding="utf-8"))
        self.assertTrue(access["train1_accessed"] and access["train2_accessed"])
        for field in (
            "train3_accessed", "train4_accessed", "test_accessed", "labels_accessed",
            "attacks_accessed", "p2_p3_p4_values_accessed", "br2_pair_results_accessed",
            "candidate_arm_evidence_visible_during_profiling", "raw_values_persisted",
            "raw_windows_persisted", "event_timestamps_publicly_persisted",
            "absolute_local_paths_persisted",
        ):
            self.assertFalse(access[field])
        self.assertFalse(fit["lower_ranked_fallback_used"])
        self.assertFalse(fit["task039d2_authorized"] or fit["rule_v2_authorized"])

    def test_arm_summary_is_fit_only_and_has_no_winner(self) -> None:
        self._documents()
        arm = json.loads((REPORTS / "TASK-039D1_ARM_FIT_SUMMARY.json").read_text(encoding="utf-8"))
        self.assertEqual([item["arm"] for item in arm["arms"]], ["META", "STAT", "GDN"])
        self.assertTrue(arm["same_pair_same_d1_outcome_across_all_origin_arms"])
        self.assertFalse(arm["d2_confirmation_metrics_calculated"] or arm["winner_selected"])

    def test_d1_itself_did_not_authorize_d2(self) -> None:
        fit = json.loads((REPORTS / "TASK-039D1_FIT_RESULT.json").read_text(encoding="utf-8"))
        self.assertFalse(fit["task039d2_authorized"])
        authorization_path = REPORTS / "TASK-039D2_AUTHORIZATION.json"
        if authorization_path.exists():
            authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
            self.assertEqual(authorization["task_id"], "TASK-039D1-AUDIT")
            self.assertFalse(authorization["d2_executed_by_this_artifact"])


if __name__ == "__main__":
    unittest.main()
