from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.v6.task039e1_audit_prep_v1 import FUTURE_REPLAY_DESIGN
from tests.task039e1_audit_support import make_exact_synthetic_dataset
from paperworks.v6.task039e1_audit_prep_v1 import (
    audit_synthetic_construction_evidence_dataset_v1,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = (
    "task039e1_independent_evidence_audit_result_v1_schema.json",
    "task039e1_future_private_ledger_replay_design_v1_schema.json",
)


class AuditSchemaDraftTests(unittest.TestCase):
    def test_closed_drafts_parse_and_match_preparation_documents(self) -> None:
        documents = (
            audit_synthetic_construction_evidence_dataset_v1(
                make_exact_synthetic_dataset()
            ).to_dict(),
            FUTURE_REPLAY_DESIGN.to_dict(),
        )
        for name, document in zip(SCHEMAS, documents, strict=True):
            with self.subTest(schema=name):
                schema = json.loads(
                    (ROOT / "schemas" / "v6" / name).read_text(encoding="utf-8")
                )
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(set(document), set(schema["required"]))
                for key, definition in schema["properties"].items():
                    if "const" in definition:
                        self.assertEqual(document[key], definition["const"])


if __name__ == "__main__":
    unittest.main()
