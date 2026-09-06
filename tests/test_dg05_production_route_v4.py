from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.dg05_connected_rehearsal_v3 import _detectors, _dispatch, _manifest, _rules, _scope
from paperworks.validation_v2.dg05_execution_closure_v1 import (
    DG05ProductionExecutorV1,
    PhysicalFileIdentityV2,
    digest,
    file_sha256,
    project_attack_feature_file_v1,
    self_hashed,
)
from paperworks.validation_v2.dg05_production_route_v4 import execute_prediction_cell_v4
from paperworks.validation_v2.multipanel_custody_v1 import FrozenPhysicalFileAuthorityV2, frozen_feature_allowlist_authorities_v2


H = "a" * 64
G = "b" * 40


def write_csv(path: Path, authority, timestamps: list[str]) -> None:
    header = [authority.timestamp_id, *authority.feature_ids, "Attack"]
    lines = [",".join(header)]
    for timestamp in timestamps:
        lines.append(",".join([timestamp, *(["1.0"] * len(authority.feature_ids)), "opaque"]))
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


class ProductionRouteV4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.detectors, self.rules, self.scope = _detectors(), _rules(), _scope()
        self.dispatch = _dispatch(self.detectors, self.rules)
        self.manifest = _manifest(self.dispatch, self.detectors, self.rules, self.scope)
        self.manifest_hash = self.manifest.document()["self_hash"]
        implementations = dict(self.manifest.implementation_hashes)
        self.executor = DG05ProductionExecutorV1.synthetic_rehearsal(
            executable_manifest=self.manifest, executable_manifest_hash=self.manifest_hash,
            detector_registry=self.detectors, dispatch_registry=self.dispatch,
            rule_runtime_registry=self.rules,
            adapter_implementation_hash=implementations["prediction_adapter"],
            fusion_implementation_hash=implementations["fusion_runtime"])
        self.predecessor = self_hashed({"schema": "dg05_executable_authority_manifest_v3",
                                        "historical_prediction_executable_manifest_hash": self.manifest_hash})
        self.release = self_hashed({"schema": "dg05_production_release_manifest_v1",
                                    "predecessor_v3_manifest_hash": self.predecessor["self_hash"]})

    def _fixture(self, root: Path, timestamps: list[str]):
        panel = next(iter(frozen_feature_allowlist_authorities_v2()))
        allowlist = frozen_feature_allowlist_authorities_v2()[panel]
        source = root / "source.csv"; write_csv(source, allowlist, timestamps)
        header = [allowlist.timestamp_id, *allowlist.feature_ids, "Attack"]
        physical_item = PhysicalFileIdentityV2(panel, "synthetic.csv", file_sha256(source), digest(header), H)
        method_id = "M0_PCA_SPE"
        dispatch_hash = self.dispatch.document()["self_hash"]
        cell = {"panel_id": panel, "file_id": physical_item.file_id, "method_id": method_id,
                "dispatch_authority_hash": dispatch_hash}
        cell["cell_id"] = digest(cell)
        destination = root / "projection.jsonl"
        projection, timestamp = project_attack_feature_file_v1(
            source=source, destination=destination, physical_file=physical_item,
            panel_authority=allowlist, file_id=physical_item.file_id,
            adapter_implementation_hash=H, source_commit=G)
        return cell, projection, timestamp, destination

    def test_release_bound_success_emits_v4_receipt(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            values = [(datetime(2026, 1, 1) + timedelta(seconds=index)).isoformat() for index in range(8)]
            cell, projection, timestamp, path = self._fixture(root, values)
            receipt = execute_prediction_cell_v4(
                cell=cell, dispatch=self.dispatch, projection=projection, timestamp=timestamp,
                release=self.release, predecessor_v3=self.predecessor, executor=self.executor,
                projection_path=path, output_directory=root / "out", source_commit=G)
            self.assertEqual(receipt.status, "SUCCESS")
            self.assertEqual(receipt.executable_manifest_hash, self.release["self_hash"])

    def test_duplicate_and_gap_never_invoke_scorer(self):
        for values, code in ((["2026-01-01T00:00:00", "2026-01-01T00:00:00"], "INVALID_TIMESTAMP_AUTHORITY_DUPLICATE"),
                             (["2026-01-01T00:00:00", "2026-01-01T00:00:02"], "INVALID_TIMESTAMP_AUTHORITY_NON_UNIT_GAP")):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                cell, projection, timestamp, path = self._fixture(root, values)
                receipt = execute_prediction_cell_v4(
                    cell=cell, dispatch=self.dispatch, projection=projection, timestamp=timestamp,
                    release=self.release, predecessor_v3=self.predecessor, executor=self.executor,
                    projection_path=path, output_directory=root / "out", source_commit=G)
                self.assertEqual((receipt.status, receipt.failure_code), ("METHOD_FAILURE", code))
                self.assertFalse((root / "out").exists())

    def test_predecessor_substitution_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            values = ["2026-01-01T00:00:00", "2026-01-01T00:00:01"]
            cell, projection, timestamp, path = self._fixture(root, values)
            changed = self_hashed({"schema": "dg05_executable_authority_manifest_v3",
                                   "historical_prediction_executable_manifest_hash": "f" * 64})
            with self.assertRaisesRegex(ValueError, "RELEASE_EXECUTION_KERNEL_BINDING_MISMATCH"):
                execute_prediction_cell_v4(
                    cell=cell, dispatch=self.dispatch, projection=projection, timestamp=timestamp,
                    release=self.release, predecessor_v3=changed, executor=self.executor,
                    projection_path=path, output_directory=root / "out", source_commit=G)


if __name__ == "__main__":
    unittest.main()
