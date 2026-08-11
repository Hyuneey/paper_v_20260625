import json
from pathlib import Path
import unittest

from paperworks.v6.task039e2_audit_prep_v1 import (
    IndependentCapabilityReceiptV1,
    IndependentE2AuditPreparationReceiptV1,
)
from task039e2_audit_support import make_configuration


class Task039E2AuditSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema_root = Path(__file__).parents[1] / "schemas" / "v6"

    def _load(self, filename: str) -> dict[str, object]:
        return json.loads(
            (self.schema_root / filename).read_text(encoding="utf-8")
        )

    def test_all_task_owned_schemas_are_valid_json_and_closed(self) -> None:
        filenames = (
            "task039e2_independent_expected_configuration_v1_schema.json",
            "task039e2_independent_capability_receipt_v1_schema.json",
            "task039e2_audit_preparation_receipt_v1_schema.json",
        )
        for filename in filenames:
            with self.subTest(filename=filename):
                schema = self._load(filename)
                self.assertEqual(schema["type"], "object")
                self.assertIs(schema["additionalProperties"], False)
                self.assertEqual(set(schema["required"]), set(schema["properties"]))

    def test_configuration_schema_freezes_exact_provider_settings(self) -> None:
        schema = self._load(
            "task039e2_independent_expected_configuration_v1_schema.json"
        )
        properties = schema["properties"]
        self.assertEqual(properties["provider"]["const"], "openai")
        self.assertEqual(
            properties["model"]["const"], "gpt-5.4-2026-03-05"
        )
        self.assertEqual(properties["temperature"]["const"], 0.7)
        self.assertEqual(properties["seed"]["type"], "null")
        self.assertEqual(
            set(make_configuration().to_dict()), set(schema["required"])
        )

    def test_receipt_contract_keys_match_serialized_records(self) -> None:
        capability_schema = self._load(
            "task039e2_independent_capability_receipt_v1_schema.json"
        )
        preparation_schema = self._load(
            "task039e2_audit_preparation_receipt_v1_schema.json"
        )
        self.assertEqual(
            set(IndependentCapabilityReceiptV1().to_dict()),
            set(capability_schema["required"]),
        )
        self.assertEqual(
            set(IndependentE2AuditPreparationReceiptV1().to_dict()),
            set(preparation_schema["required"]),
        )


if __name__ == "__main__":
    unittest.main()
