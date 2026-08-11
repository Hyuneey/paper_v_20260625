from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from paperworks.v6.task039e1_final_audit_v1 import (
    build_audit_artifact_v1,
    build_e2_authorization_v1,
    schema_documents_v1,
)


ROOT = Path(__file__).resolve().parents[1]


class FinalAuditSchemaTests(unittest.TestCase):
    def test_committed_schemas_equal_independent_generator(self) -> None:
        for name, generated in schema_documents_v1().items():
            committed = json.loads(
                (ROOT / "schemas/v6" / f"{name}_schema.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(generated, committed)
            self.assertFalse(committed["additionalProperties"])

    def test_result_instances_validate_and_unknown_fields_fail(self) -> None:
        try:
            import jsonschema
        except ModuleNotFoundError:
            self.skipTest("jsonschema environment unavailable")
        schemas = schema_documents_v1()
        e2 = build_e2_authorization_v1()
        audit = build_audit_artifact_v1(
            audit_execution_code_commit="1" * 40,
            audit_replay_ledger_hash="2" * 64,
            e2_authorization_hash=e2["artifact_hash"],
        )
        for name, document in (
            ("task039e1_final_audit_v1", audit),
            ("task039e2_authorization_v1", e2),
        ):
            validator = jsonschema.Draft202012Validator(schemas[name])
            self.assertEqual([], list(validator.iter_errors(document)))
            altered = copy.deepcopy(document)
            altered["unknown"] = True
            self.assertTrue(list(validator.iter_errors(altered)))


if __name__ == "__main__":
    unittest.main()
