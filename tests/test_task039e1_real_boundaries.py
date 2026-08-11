from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperworks.v6.task039e1_evidence_materialization_v1 import (
    E1_AUTHORIZATION_HASH,
    PreregisteredWindowConstantBundleV1,
    SCHEMA_FILES,
    TASK039E1Error,
    assert_public_payload_safe_v1,
    schema_documents_v1,
    validate_e1_authorization_v1,
    validate_external_roots_v1,
    verify_self_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]


class RealBoundaryTests(unittest.TestCase):
    def test_exact_authorization_and_window_constants(self):
        document = json.loads((ROOT / "docs/task_reports/TASK-039E1_AUTHORIZATION.json").read_text(encoding="utf-8"))
        validate_e1_authorization_v1(document)
        self.assertEqual(verify_self_hash_v1(document), E1_AUTHORIZATION_HASH)
        window = PreregisteredWindowConstantBundleV1()
        self.assertEqual((window.source_pre_window_seconds, window.target_response_window_seconds), (5, 3))
        self.assertFalse(window.to_dict()["runtime_authority"])

    def test_authorization_rejects_added_authority(self):
        document = json.loads((ROOT / "docs/task_reports/TASK-039E1_AUTHORIZATION.json").read_text(encoding="utf-8"))
        document["llm_calls_authorized"] = True
        with self.assertRaises(TASK039E1Error):
            validate_e1_authorization_v1(document)

    def test_roots_are_external_distinct_and_traversal_free(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            d1, d2, e1 = base / "d1", base / "d2", base / "e1"
            d1.mkdir(); d2.mkdir()
            observed = validate_external_roots_v1(
                repository_root=ROOT, d1_private_value=str(d1),
                d2_private_value=str(d2), e1_private_value=str(e1),
            )
            self.assertEqual(len(set(observed)), 3)
            with self.assertRaises(TASK039E1Error):
                validate_external_roots_v1(
                    repository_root=ROOT, d1_private_value=str(d1),
                    d2_private_value=str(d1), e1_private_value=str(e1),
                )

    def test_public_payload_rejects_private_values_and_absolute_paths(self):
        with self.assertRaises(TASK039E1Error):
            assert_public_payload_safe_v1({"source_step_threshold": 1.0})
        with self.assertRaises(TASK039E1Error):
            assert_public_payload_safe_v1({"path": "C:\\private\\ledger.json"})

    def test_real_schema_inventory_is_strict(self):
        schemas = schema_documents_v1()
        self.assertEqual(set(schemas), set(SCHEMA_FILES))
        for schema in schemas.values():
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])

    def test_real_module_has_no_hai_loader_or_provider(self):
        source = (ROOT / "src/paperworks/v6/task039e1_evidence_materialization_v1.py").read_text(encoding="utf-8")
        self.assertNotIn("load_authorized_train", source)
        self.assertNotIn("HAI_DATA_ROOT", source)
        self.assertNotIn("provider", source.lower())


if __name__ == "__main__":
    unittest.main()
