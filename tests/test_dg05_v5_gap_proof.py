from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1
from paperworks.validation_v2.dg05_metric_surface_v1 import canonical_bytes, self_hashed
from paperworks.validation_v2.dg05_upstream_lineage_verifier_v2 import (
    UpstreamPanelReplayPathsV2,
    reconstruct_metric_primitive_from_upstream_v2,
)
from paperworks.validation_v2.multipanel_custody_v1 import FROZEN_PANEL_ORDER_V2


H = "a" * 64
G = "b" * 40


def persist(path: Path, value: dict) -> Path:
    path.write_bytes(canonical_bytes(value) + b"\n")
    return path


class V4GapProofTests(unittest.TestCase):
    """Executable counterexamples retained as historical V4 gap evidence."""

    def _fixture(self, root: Path, *, interval_start: str = "2026-01-01T00:00:00",
                 primary_status: str = "P1_ELIGIBLE"):
        panel = FROZEN_PANEL_ORDER_V2[0]
        methods = tuple(FROZEN_METHOD_IDS_BY_PANEL_V1[panel])
        projection = root / "projection.jsonl"
        projection.write_bytes(
            b'["timestamp","P1_FCV01D"]\n'
            b'["2026-01-01T00:00:00",1.0]\n'
            b'["2026-01-01T00:00:01",1.0]\n'
            b'["2026-01-01T00:00:02",1.0]\n'
        )
        projection_hash = sha256(projection.read_bytes()).hexdigest()
        receipts = [
            {
                "cell_id": sha256(method.encode("ascii")).hexdigest(),
                "panel_id": panel,
                "file_id": "F1",
                "method_id": method,
                "projection_hash": projection_hash,
                "row_count": 3,
                "status": "METHOD_FAILURE",
            }
            for method in methods
        ]
        manifest = self_hashed({
            "schema": "global_prediction_manifest_v3",
            "executable_approval_manifest_hash": H,
            "receipts": receipts,
        })
        freeze = self_hashed({
            "schema": "global_prediction_freeze_v3",
            "manifest_hash": manifest["self_hash"],
            "executable_approval_manifest_hash": H,
        })
        scenario_record = self_hashed({
            "panel_id": panel,
            "scenario_id": "S1",
            "file_id": "F1",
            "closed_intervals": [[interval_start, "2026-01-01T00:00:02"]],
        })
        scenario = self_hashed({
            "schema": "frozen_scenario_authority_v1",
            "global_freeze_hash": freeze["self_hash"],
            "records": [scenario_record],
        })
        eligibility = self_hashed({
            "panel_id": panel,
            "scenario_id": "S1",
            "scenario_record_hash": scenario_record["self_hash"],
            "primary_status": primary_status,
        })
        denominator = self_hashed({
            "schema": "denominator_authority_v1",
            "scenario_authority_hash": scenario["self_hash"],
            "records": [eligibility],
        })
        registry = self_hashed({
            "schema": "normal_burden_source_registry_v2",
            "required_components": [],
            "components": [],
            "component_count": 0,
        })
        docs = {
            "manifest": manifest,
            "freeze": freeze,
            "scenario": scenario,
            "denominator": denominator,
            "registry": registry,
        }
        for name, value in docs.items():
            persist(root / f"{name}.json", value)
        paths = UpstreamPanelReplayPathsV2(
            root / "manifest.json", root / "freeze.json", root / "scenario.json",
            root / "denominator.json", {"F1": projection}, {}, {},
            root / "registry.json", {}, root / "asserted.json")
        normal = {
            "schema": "normal_burden_independent_replay_v2",
            "status": "PASS",
            "methods": [
                {
                    "panel_id": panel,
                    "method_id": method,
                    "authority_class": "GUARD_CONDITIONED_NORMAL",
                    "components": [],
                    "false_seconds": 0,
                    "false_episodes": 0,
                    "exposure_seconds": 1,
                    "false_seconds_per_hour": 0.0,
                    "false_episodes_per_hour": 0.0,
                }
                for method in methods
            ],
        }
        return panel, paths, registry, freeze, normal

    def _reconstruct(self, root: Path, **changes):
        panel, paths, registry, freeze, normal = self._fixture(root, **changes)
        with patch(
            "paperworks.validation_v2.dg05_upstream_lineage_verifier_v2.replay_normal_source_registry_v2",
            return_value=normal,
        ):
            primitive = reconstruct_metric_primitive_from_upstream_v2(
                panel_id=panel,
                paths=paths,
                expected_release_manifest_hash=H,
                expected_dec031_binding_hash="9" * 64,
                expected_normal_source_registry_hash=registry["self_hash"],
                expected_global_freeze_hash=freeze["self_hash"],
                source_commit=G,
            )
        return primitive, paths

    def test_v4_accepts_coherent_scenario_and_denominator_rehash(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            original, _ = self._reconstruct(Path(first))
            changed, _ = self._reconstruct(
                Path(second), interval_start="2026-01-01T00:00:01", primary_status="OUT_OF_SCOPE")
        self.assertNotEqual(original["self_hash"], changed["self_hash"])
        self.assertNotEqual(original["scenarios"], changed["scenarios"])

    def test_v4_raw_source_and_custodian_roots_are_not_verifier_inputs(self):
        fields = set(UpstreamPanelReplayPathsV2.__dataclass_fields__)
        required_missing = {
            "raw_physical_paths", "physical_file_authority_path", "projection_authority_paths",
            "timestamp_authority_paths", "raw_scenario_source_paths", "custodian_policy_path",
            "custodian_request_path", "lease_consumed_path", "custodian_invocation_path",
            "custodian_output_path", "full_process_scope_path",
        }
        self.assertTrue(required_missing.isdisjoint(fields))
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            disconnected = root / "raw-source.csv"
            disconnected.write_bytes(b"changed-but-unreferenced\n")
            primitive, _ = self._reconstruct(root)
            self.assertEqual(primitive["schema"], "metric_surface_primitives_v2")


if __name__ == "__main__":
    unittest.main()
