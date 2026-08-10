from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.v6.common import stable_hash_v1


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_INSTANCE_PAIRS = (
    (
        ROOT / "schemas/v6/gdn_candidate_result_v1_schema.json",
        ROOT / "docs/task_reports/TASK-039C_GDN_RESULT.json",
    ),
    (
        ROOT / "schemas/v6/task039c_gdn_environment_receipt_v1_schema.json",
        ROOT / "docs/task_reports/TASK-039C_GDNR_ENVIRONMENT_RECEIPT.json",
    ),
    (
        ROOT / "schemas/v6/task039c_gdnr_data_access_audit_v1_schema.json",
        ROOT / "docs/task_reports/TASK-039C_GDNR_DATA_ACCESS_AUDIT.json",
    ),
    (
        ROOT / "schemas/v6/task039c_gdnr_execution_receipt_v1_schema.json",
        ROOT / "docs/task_reports/TASK-039C_GDNR_EXECUTION_RECEIPT.json",
    ),
)


class Task039CGDNRemediationSchemaTests(unittest.TestCase):
    def test_all_remediation_schemas_are_draft_2020_12_valid(self) -> None:
        for schema_path, _ in SCHEMA_INSTANCE_PAIRS:
            with self.subTest(schema=schema_path.name):
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)

    def test_available_public_instances_validate_and_self_hash(self) -> None:
        for schema_path, instance_path in SCHEMA_INSTANCE_PAIRS:
            if not instance_path.exists():
                continue
            with self.subTest(instance=instance_path.name):
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                instance = json.loads(instance_path.read_text(encoding="utf-8"))
                Draft202012Validator(schema).validate(instance)
                observed = instance.pop("artifact_hash")
                self.assertEqual(stable_hash_v1(instance), observed)


if __name__ == "__main__":
    unittest.main()
