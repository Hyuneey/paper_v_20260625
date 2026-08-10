from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.gdn.pyg_port_compatibility_v1 import (
    BASE_COMMIT,
    COMPATIBILITY_STATUS,
    PYG15_COMMIT,
    PYG28_COMMIT,
    api_drift_rows_v1,
    assert_gdnp_patch_scope_v1,
    build_api_drift_matrix_v1,
    build_source_inventories_v1,
    confirm_node_dim_root_cause_v1,
)


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = os.environ.get("TASK039C_GDN_UPSTREAM_ROOT")
PYG_SOURCE = os.environ.get("TASK039C_GDN_PYG_SOURCE_ROOT")


class Task039CGDNPAPIAuditTests(unittest.TestCase):
    def test_twenty_rows_are_complete_and_resolved(self) -> None:
        rows = api_drift_rows_v1()
        self.assertEqual([row["row"] for row in rows], list(range(1, 21)))
        self.assertEqual(len(rows), 20)
        self.assertNotIn("unresolved", {row["classification"] for row in rows})
        self.assertEqual(sum(row["classification"] == "exact_semantics" for row in rows), 17)

    def test_frozen_tag_and_base_identities(self) -> None:
        self.assertEqual(BASE_COMMIT, "932c3c7e58e853959b006a6a023743620dd4457d")
        self.assertEqual(PYG15_COMMIT, "cc071b7c4bd632ace8919a81d7049b984e09f0ba")
        self.assertEqual(PYG28_COMMIT, "726310a486eae37a89cd6359072b82bbbbb71579")

    def test_patch_scope_is_only_explicit_node_dimension(self) -> None:
        self.assertRegex(assert_gdnp_patch_scope_v1(repository_root=ROOT), r"^[0-9a-f]{64}$")

    @unittest.skipUnless(UPSTREAM and PYG_SOURCE, "official source roots are external")
    def test_official_source_inventory_and_root_cause(self) -> None:
        source = build_source_inventories_v1(
            upstream_root=Path(UPSTREAM),
            pyg_source_root=Path(PYG_SOURCE),
        )
        matrix = build_api_drift_matrix_v1(
            source_inventories=source,
            created_at="2026-08-11T00:00:00+00:00",
        )
        cause = confirm_node_dim_root_cause_v1(
            repository_root=ROOT,
            upstream_root=Path(UPSTREAM),
            pyg_source_root=Path(PYG_SOURCE),
        )
        self.assertEqual(matrix["status"], COMPATIBILITY_STATUS)
        self.assertEqual(matrix["unresolved_rows"], [])
        self.assertTrue(cause["confirmed"])

    def test_new_schemas_are_valid(self) -> None:
        for name in (
            "gdn_api_drift_matrix_v1_schema.json",
            "gdn_index_semantics_receipt_v1_schema.json",
            "gdn_port_compatibility_closure_receipt_v1_schema.json",
            "gdn_legacy_oracle_receipt_v1_schema.json",
        ):
            with self.subTest(name=name):
                schema = json.loads((ROOT / "schemas" / "v6" / name).read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)


if __name__ == "__main__":
    unittest.main()
