from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.profiling.task039d2_result_recovery_v1 import (
    COMMIT_A_SCIENTIFIC_SOURCE_HASHES,
    verify_recovery_self_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
SCHEMAS = ROOT / "schemas" / "v6"

ARTIFACTS = {
    "TASK-039D2_DIRECTIONAL_CONFIRMATION_SUMMARY.json": "task039d2_directional_confirmation_summary_v1_schema.json",
    "TASK-039D2_PAIR_CONFIRMATION_SUMMARY.json": "task039d2_pair_confirmation_summary_v1_schema.json",
    "TASK-039D2_ARM_CONFIRMATION_SUMMARY.json": "task039d2_arm_confirmation_summary_v1_schema.json",
    "TASK-039D2_RESULT.json": "task039d2_result_v1_schema.json",
    "TASK-039D2_DATA_ACCESS_AUDIT.json": "task039d2r_data_access_audit_v1_schema.json",
    "TASK-039D2_EXECUTION_RECEIPT.json": "task039d2_real_execution_receipt_v1_schema.json",
    "TASK-039D2R_RESULT_CONTRACT_RECOVERY_RECEIPT.json": "task039d2_result_contract_recovery_receipt_v1_schema.json",
    "TASK-039D2_FAILED_RUN_CUSTODY.json": "task039d2_failed_run_custody_v1_schema.json",
}

EXPECTED_ARM_COUNTS = {
    "META": {"pairs": 15, "directions": 28, "sources": 7, "targets": 9},
    "STAT": {"pairs": 17, "directions": 32, "sources": 8, "targets": 8},
    "GDN": {"pairs": 3, "directions": 5, "sources": 3, "targets": 3},
}
EXPECTED_OVERLAP_COUNTS = {
    "META_only": 4,
    "STAT_only": 5,
    "GDN_only": 2,
    "META_STAT_only": 11,
    "META_GDN_only": 0,
    "STAT_GDN_only": 1,
    "all_three": 0,
}


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class TASK039D2RResultInstanceTests(unittest.TestCase):
    def test_all_recovered_artifacts_are_closed_valid_and_self_hashed(self) -> None:
        for artifact_name, schema_name in ARTIFACTS.items():
            with self.subTest(artifact=artifact_name):
                document = _load(REPORTS / artifact_name)
                schema = _load(SCHEMAS / schema_name)
                Draft202012Validator.check_schema(schema)
                Draft202012Validator(schema).validate(document)
                self.assertEqual(verify_recovery_self_hash_v1(document), document["artifact_hash"])

    def test_reconstruction_counts_and_arm_metrics_are_exact(self) -> None:
        result = _load(REPORTS / "TASK-039D2_RESULT.json")
        pair = _load(REPORTS / "TASK-039D2_PAIR_CONFIRMATION_SUMMARY.json")
        arm = _load(REPORTS / "TASK-039D2_ARM_CONFIRMATION_SUMMARY.json")
        self.assertEqual(result["confirmed_directional_count"], 42)
        self.assertEqual(result["conflict_directional_count"], 3)
        self.assertEqual(result["pairs_with_confirmed_direction_count"], 23)
        self.assertEqual(pair["d1_supported_pairs_without_confirmed_direction_count"], 2)
        by_arm = {item["arm"]: item for item in arm["arms"]}
        for name, expected in EXPECTED_ARM_COUNTS.items():
            self.assertEqual(by_arm[name]["d2_confirmed_pair_count"], expected["pairs"])
            self.assertEqual(by_arm[name]["directional_confirmation_count"], expected["directions"])
            self.assertEqual(by_arm[name]["distinct_confirmed_source_count"], expected["sources"])
            self.assertEqual(by_arm[name]["distinct_confirmed_target_count"], expected["targets"])
        overlap = arm["confirmed_pair_overlap"]
        for name, expected in EXPECTED_OVERLAP_COUNTS.items():
            self.assertEqual(overlap[name]["count"], expected)

    def test_receipt_preserves_commit_a_and_exact_four_source_map(self) -> None:
        receipt = _load(REPORTS / "TASK-039D2_EXECUTION_RECEIPT.json")
        recovery = _load(REPORTS / "TASK-039D2R_RESULT_CONTRACT_RECOVERY_RECEIPT.json")
        self.assertEqual(receipt["execution_code_commit"], "5524262d8a666093f948f7f01491b4a0b03e568e")
        self.assertEqual(receipt["scientific_source_hashes"], COMMIT_A_SCIENTIFIC_SOURCE_HASHES)
        self.assertTrue(recovery["scientific_sources_unchanged"])
        self.assertFalse(recovery["scientific_code_changed"])
        self.assertFalse(recovery["train3_reread"])
        self.assertFalse(recovery["hai_values_accessed_during_recovery"])

    def test_access_and_authority_boundaries_are_explicit(self) -> None:
        access = _load(REPORTS / "TASK-039D2_DATA_ACCESS_AUDIT.json")
        result = _load(REPORTS / "TASK-039D2_RESULT.json")
        original = access["original_scientific_run"]
        recovery = access["recovery_finalization"]
        self.assertTrue(original["train3_accessed"])
        self.assertFalse(original["train1_feature_values_accessed"])
        self.assertFalse(original["train2_feature_values_accessed"])
        self.assertFalse(recovery["train3_accessed"])
        self.assertFalse(recovery["train3_reread"])
        self.assertFalse(recovery["hai_feature_values_accessed"])
        self.assertFalse(result["winner_selected"])
        self.assertFalse(result["rule_v2_authorized"])
        self.assertFalse(result["agent_authorized"])
        self.assertFalse(result["runtime_authority"])

    def test_public_outputs_contain_no_absolute_local_path(self) -> None:
        windows_absolute = re.compile(r"[A-Za-z]:[\\/]")
        for artifact_name in ARTIFACTS:
            text = (REPORTS / artifact_name).read_text(encoding="utf-8")
            self.assertIsNone(windows_absolute.search(text), artifact_name)


if __name__ == "__main__":
    unittest.main()
