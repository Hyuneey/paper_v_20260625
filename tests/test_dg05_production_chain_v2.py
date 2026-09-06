from __future__ import annotations

import json
from pathlib import Path
import unittest

from paperworks.validation_v2.dg05_production_chain_v2 import (
    DG05ProductionChainV2Error,
    REQUIRED_IMPLEMENTATION_ROLES_V5,
    initialize_production_release_v5,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/dg05_v8_release"
V4 = ROOT / "research_control_center/validation_v2/dg05_v4_release/DG05_EXECUTABLE_AUTHORITY_MANIFEST_V4.json"
V4_CLOSURE = ROOT / "research_control_center/validation_v2/dg05_v4_release/DG05_EXECUTABLE_CLOSURE_AUTHORITY_V4.json"


class ProductionChainV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = OUT / "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V8.json"
        self.release = json.loads(self.path.read_text(encoding="ascii"))

    def test_v8_manifest_binds_complete_implementation_and_frozen_predecessor(self) -> None:
        self.assertEqual(self.release["executable_version"], "DG05_EXECUTABLE_V8")
        self.assertEqual(
            {row["logical_name"] for row in self.release["implementation_authorities"]},
            REQUIRED_IMPLEMENTATION_ROLES_V5,
        )
        self.assertEqual(self.release["attack_test_accesses"], 0)
        self.assertEqual(self.release["label_scenario_accesses"], 0)
        state = initialize_production_release_v5(
            release_manifest_path=self.path, repository_root=ROOT,
            predecessor_v4_manifest_path=V4, predecessor_v4_closure_path=V4_CLOSURE,
            expected_release_hash=self.release["self_hash"],
            authority_mode="PREACCESS_FROZEN_KERNEL_REHEARSAL",
            expected_executable_version="DG05_EXECUTABLE_V8",
        )
        self.assertFalse(state["protected_access_authorized"])
        self.assertEqual(state["data_access_mode"], "SYNTHETIC_ONLY_NO_PROTECTED_DISCOVERY")

    def test_production_initialization_requires_exact_future_user_approval(self) -> None:
        with self.assertRaisesRegex(DG05ProductionChainV2Error, "EXACT_V5_USER_APPROVAL_REQUIRED"):
            initialize_production_release_v5(
                release_manifest_path=self.path, repository_root=ROOT,
                predecessor_v4_manifest_path=V4, predecessor_v4_closure_path=V4_CLOSURE,
                expected_release_hash=self.release["self_hash"], authority_mode="PRODUCTION",
                expected_executable_version="DG05_EXECUTABLE_V8",
            )
        state = initialize_production_release_v5(
            release_manifest_path=self.path, repository_root=ROOT,
            predecessor_v4_manifest_path=V4, predecessor_v4_closure_path=V4_CLOSURE,
            expected_release_hash=self.release["self_hash"], authority_mode="PRODUCTION",
            user_approved_release_hash=self.release["self_hash"],
            expected_executable_version="DG05_EXECUTABLE_V8",
        )
        self.assertTrue(state["protected_access_authorized"])

    def test_public_execution_receipts_are_complete_and_fail_closed(self) -> None:
        rehearsal = json.loads((OUT / "SYNTHETIC_DG05_PRODUCTION_ROUTE_REHEARSAL_V8.json").read_text(encoding="ascii"))
        parity = json.loads((OUT / "PRODUCTION_KERNEL_PARITY_V1.json").read_text(encoding="ascii"))
        roots = json.loads((OUT / "ROOT_TO_RESULT_REPLAY_V1.json").read_text(encoding="ascii"))
        self.assertEqual((rehearsal["derived_prediction_cells"], rehearsal["metric_surface_count"]), (72, 228))
        self.assertEqual(parity["production_kernel_invocation_count"], 72)
        self.assertEqual(parity["synthetic_fallback_invocation_count"], 0)
        self.assertTrue(all(roots["per_root_replay"].values()))
        self.assertEqual(roots["root_covered_surface_count"], 228)

    def test_transitive_implementation_authority_is_exactly_bound(self) -> None:
        reference = self.release["transitive_implementation_authority"]
        authority = json.loads((ROOT / reference["relative_path"]).read_text(encoding="ascii"))
        self.assertEqual(reference["self_hash"], authority["self_hash"])
        self.assertEqual(reference["closure_count"], authority["closure_count"])
        self.assertGreaterEqual(authority["closure_count"], 100)
        paths = {row["relative_path"] for row in authority["implementations"]}
        self.assertIn("src/paperworks/validation_v2/pca_spe_v2.py", paths)
        self.assertIn("src/paperworks/validation_v2/isolation_forest_v1.py", paths)
        self.assertIn("src/paperworks/validation_v2/formal_v4_authority_v1.py", paths)


if __name__ == "__main__":
    unittest.main()
