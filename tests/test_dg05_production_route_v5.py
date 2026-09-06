from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from paperworks.validation_v2.dg05_connected_rehearsal_v3 import _detectors, _dispatch, _manifest, _rules, _scope
from paperworks.validation_v2.dg05_execution_closure_v1 import (
    DG05ProductionExecutorV1, PhysicalFileIdentityV2, digest, file_sha256,
    project_attack_feature_file_v1, self_hashed,
)
from paperworks.validation_v2.dg05_production_route_v5 import (
    KernelInvocationCensusV5, execute_prediction_cell_v5, validate_release_execution_kernel_v5,
)
from paperworks.validation_v2.multipanel_custody_v1 import frozen_feature_allowlist_authorities_v2


H = "a" * 64
G = "b" * 40


def write_csv(path: Path, authority, timestamps: list[str]) -> None:
    header = [authority.timestamp_id, *authority.feature_ids, "Attack"]
    lines = [",".join(header)]
    for timestamp in timestamps:
        lines.append(",".join([timestamp, *(["1.0"] * len(authority.feature_ids)), "opaque"]))
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


class ProductionRouteV5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.detectors, self.rules, scope = _detectors(), _rules(), _scope()
        self.dispatch = _dispatch(self.detectors, self.rules)
        self.manifest = _manifest(self.dispatch, self.detectors, self.rules, scope)
        implementations = dict(self.manifest.implementation_hashes)
        self.executor = DG05ProductionExecutorV1.synthetic_rehearsal(
            executable_manifest=self.manifest,
            executable_manifest_hash=self.manifest.document()["self_hash"],
            detector_registry=self.detectors, dispatch_registry=self.dispatch,
            rule_runtime_registry=self.rules,
            adapter_implementation_hash=implementations["prediction_adapter"],
            fusion_implementation_hash=implementations["fusion_runtime"],
        )
        self.predecessor = self_hashed({"schema": "dg05_executable_authority_manifest_v3"})
        self.release = self_hashed({
            "schema": "dg05_production_release_manifest_v2",
            "executable_version": "DG05_EXECUTABLE_V5", "historical_execution_kernel_hash": H,
            "readiness": "READY_FOR_USER_REAPPROVAL", "source_commit": G,
        })
        self.initialized = {
            "release_manifest_hash": self.release["self_hash"],
            "authority_mode": "PREACCESS_FROZEN_KERNEL_REHEARSAL",
            "data_access_mode": "SYNTHETIC_ONLY_NO_PROTECTED_DISCOVERY",
            "protected_access_authorized": False,
            "execution_kernel_identity": "FROZEN_PRODUCTION_SCIENTIFIC_KERNEL_V1",
        }

    def _fixture(self, root: Path, timestamps: list[str]):
        panel = next(iter(frozen_feature_allowlist_authorities_v2()))
        allowlist = frozen_feature_allowlist_authorities_v2()[panel]
        source = root / "source.csv"
        write_csv(source, allowlist, timestamps)
        physical = PhysicalFileIdentityV2(
            panel, "synthetic.csv", file_sha256(source),
            digest([allowlist.timestamp_id, *allowlist.feature_ids, "Attack"]), H,
        )
        cell = {"panel_id": panel, "file_id": physical.file_id, "method_id": "M0_PCA_SPE",
                "dispatch_authority_hash": self.dispatch.document()["self_hash"]}
        cell["cell_id"] = digest(cell)
        destination = root / "projection.jsonl"
        projection, timestamp = project_attack_feature_file_v1(
            source=source, destination=destination, physical_file=physical,
            panel_authority=allowlist, file_id=physical.file_id,
            adapter_implementation_hash=H, source_commit=G)
        return cell, projection, timestamp, destination

    def test_release_route_invokes_frozen_kernel_and_never_synthetic_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            times = [(datetime(2026, 1, 1) + timedelta(seconds=i)).isoformat() for i in range(2)]
            cell, projection, timestamp, path = self._fixture(root, times)
            census = KernelInvocationCensusV5()
            with (
                patch("paperworks.validation_v2.dg05_production_route_v5.validate_release_execution_kernel_v5"),
                patch("paperworks.validation_v2.dg05_production_route_v5.execute_normal_method_v4",
                      return_value=((False, True), None)) as kernel,
            ):
                receipt = execute_prediction_cell_v5(
                    cell=cell, dispatch=self.dispatch, projection=projection, timestamp=timestamp,
                    release=self.release, predecessor_v3=self.predecessor,
                    initialized_release_state=self.initialized, executor=self.executor,
                    projection_path=path, output_directory=root / "out", source_commit=G,
                    repository_root=Path.cwd(), invocation_census=census)
            self.assertEqual(receipt.status, "SUCCESS")
            kernel.assert_called_once()
            self.assertTrue(census.rows[0]["production_kernel_invocation"])
            self.assertFalse(census.rows[0]["synthetic_fallback_invocation"])

    def test_invalid_timeline_fails_before_frozen_kernel(self) -> None:
        for times in (["2026-01-01T00:00:00", "2026-01-01T00:00:00"],
                      ["2026-01-01T00:00:00", "2026-01-01T00:00:02"]):
            with self.subTest(times=times), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                cell, projection, timestamp, path = self._fixture(root, times)
                with (
                    patch("paperworks.validation_v2.dg05_production_route_v5.validate_release_execution_kernel_v5"),
                    patch("paperworks.validation_v2.dg05_production_route_v5.execute_normal_method_v4") as kernel,
                ):
                    receipt = execute_prediction_cell_v5(
                        cell=cell, dispatch=self.dispatch, projection=projection, timestamp=timestamp,
                        release=self.release, predecessor_v3=self.predecessor,
                        initialized_release_state=self.initialized, executor=self.executor,
                        projection_path=path, output_directory=root / "out", source_commit=G,
                        repository_root=Path.cwd(), invocation_census=KernelInvocationCensusV5())
                self.assertEqual(receipt.status, "METHOD_FAILURE")
                kernel.assert_not_called()

    def test_approved_production_mode_uses_same_route_kernel_contract(self) -> None:
        executor = object.__new__(DG05ProductionExecutorV1)
        object.__setattr__(executor, "authority_mode", "PRODUCTION")
        production = {
            "release_manifest_hash": self.release["self_hash"],
            "authority_mode": "PRODUCTION",
            "data_access_mode": "PROTECTED_DATA_ACCESS_REQUIRES_EXACT_USER_APPROVAL",
            "protected_access_authorized": True,
            "execution_kernel_identity": "FROZEN_PRODUCTION_SCIENTIFIC_KERNEL_V1",
        }
        with patch.object(DG05ProductionExecutorV1, "validate", autospec=True) as validate:
            validate_release_execution_kernel_v5(
                release=self.release, predecessor_v3=self.predecessor,
                initialized_release_state=production, executor=executor)
        validate.assert_called_once_with(executor)


if __name__ == "__main__":
    unittest.main()
