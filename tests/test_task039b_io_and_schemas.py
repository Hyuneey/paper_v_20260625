from __future__ import annotations

import json
import unittest
from pathlib import Path

from paperworks.feasibility.hai_process_io_v1 import (
    extract_manual_variable_entries,
    process_feature_names,
)
from paperworks.feasibility.hai_process_v1 import (
    HAIFeasibilityError,
    canonical_self_hash,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]


class Task039BIOAndSchemaTests(unittest.TestCase):
    def test_process_prefix_isolation_excludes_p2_p4(self) -> None:
        header = ("timestamp", "P1_A", "P2_B", "P3_C", "P4_D")
        self.assertEqual(process_feature_names(header, "P1"), ("P1_A",))
        self.assertEqual(process_feature_names(header, "P3"), ("P3_C",))

    def test_unknown_process_rejected(self) -> None:
        with self.assertRaises(HAIFeasibilityError):
            process_feature_names(("P2_A",), "P2")

    def test_manual_extraction_is_bounded_and_exact_tag_based(self) -> None:
        entries = extract_manual_variable_entries(
            page_texts=("Table\nP1_FT01 Flow transmitter unit: L/s\nP1_OTHER unrelated",),
            variable_names=("P1_FT01", "P3_MISSING"),
        )
        self.assertEqual(entries["P1_FT01"].page_references, (1,))
        self.assertEqual(entries["P3_MISSING"].page_references, ())
        self.assertLessEqual(len(entries["P1_FT01"].description), 320)

    def test_all_task039b_schemas_registered_and_closed(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        expected = {
            "hai_variable_metadata_v2",
            "hai_variable_domain_diagnostic_v1",
            "hai_delayed_response_screening_v1",
            "hai_process_feasibility_v1",
            "hai_process_selection_result_v1",
            "hai_process_freeze_v1",
            "hai_gdn_view_readiness_v1",
            "task039b_data_access_audit_v1",
        }
        self.assertTrue(expected.issubset(registry.artifact_types))
        for name in expected:
            self.assertFalse(registry.schema_for(name)["additionalProperties"])

    def test_config_self_hash(self) -> None:
        path = ROOT / "configs/v6/task039b_hai_p1_p3_feasibility.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(document["config_hash"], canonical_self_hash(document, "config_hash"))

    def test_no_real_hai_fixture_is_embedded(self) -> None:
        for path in (
            ROOT / "tests/test_task039b_contracts.py",
            ROOT / "tests/test_task039b_screening.py",
            ROOT / "tests/test_task039b_selection_and_access.py",
            ROOT / "tests/test_task039b_io_and_schemas.py",
        ):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("20" + "22-", text)
            self.assertNotIn(
                "hai-" + "test",
                text if path.name != "test_task039b_selection_and_access.py" else "",
            )


if __name__ == "__main__":
    unittest.main()
