from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.v6.task039e1_evidence_materialization_v1 import SCHEMA_FILES, schema_documents_v1


ROOT = Path(__file__).resolve().parents[1]


class RealSchemaTests(unittest.TestCase):
    def test_committed_schemas_equal_generator(self):
        generated = schema_documents_v1()
        for name, relative in SCHEMA_FILES.items():
            committed = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual(committed, generated[name])

    def test_unknown_field_rejected_when_jsonschema_available(self):
        try:
            import jsonschema
        except ModuleNotFoundError:
            self.skipTest("jsonschema environment unavailable")
        for schema in schema_documents_v1().values():
            jsonschema.Draft202012Validator.check_schema(schema)


if __name__ == "__main__":
    unittest.main()
