from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.gdn.pyg_port_compatibility_v1 import (
    verify_self_hashed_compatibility_artifact_v1,
)


ROOT = Path(__file__).resolve().parents[1]
PAIRS = (
    ("gdn_api_drift_matrix_v1_schema.json", "TASK-039C_GDNP_API_DRIFT_MATRIX.json"),
    ("gdn_index_semantics_receipt_v1_schema.json", "TASK-039C_GDNP_INDEX_SEMANTICS_RECEIPT.json"),
    ("gdn_port_compatibility_closure_receipt_v1_schema.json", "TASK-039C_GDNP_COMPATIBILITY_RECEIPT.json"),
    ("gdn_legacy_oracle_receipt_v1_schema.json", "TASK-039C_GDNP_LEGACY_ORACLE_RECEIPT.json"),
    ("task039c_gdnp_data_access_audit_v1_schema.json", "TASK-039C_GDNP_DATA_ACCESS_AUDIT.json"),
    ("task039c_gdnp_execution_receipt_v1_schema.json", "TASK-039C_GDNP_EXECUTION_RECEIPT.json"),
    ("gdn_candidate_result_v1_schema.json", "TASK-039C_GDN_RESULT.json"),
)


class Task039CGDNPResultTests(unittest.TestCase):
    def test_available_instances_validate_and_self_hash(self) -> None:
        for schema_name, instance_name in PAIRS:
            instance_path = ROOT / "docs" / "task_reports" / instance_name
            if not instance_path.exists():
                continue
            with self.subTest(instance=instance_name):
                schema = json.loads((ROOT / "schemas" / "v6" / schema_name).read_text(encoding="utf-8"))
                instance = json.loads(instance_path.read_text(encoding="utf-8"))
                Draft202012Validator(schema).validate(instance)
                verify_self_hashed_compatibility_artifact_v1(instance)

    def test_execution_runner_contains_only_frozen_seed_and_data_boundaries(self) -> None:
        source = (ROOT / "scripts/run_task039c_gdnp.py").read_text(encoding="utf-8")
        self.assertIn("FROZEN_SEEDS", source)
        self.assertIn("ALLOWED_VALUE_FILES", source)
        self.assertIn("aggregation_denominator\": 3", source)
        self.assertIn("br2_pair_supervision_used\": False", source)
        self.assertIn("meta_output_used\": False", source)
        self.assertIn("stat_output_used\": False", source)
        self.assertNotIn("TASK-039C_META_RESULT", source)
        self.assertNotIn("TASK-039C_STAT_RESULT", source)
        self.assertLess(
            source.index("train_upstream_aligned_seed_v1("),
            source.index("aggregate_and_rank_gdn_candidates_v1("),
        )


if __name__ == "__main__":
    unittest.main()
