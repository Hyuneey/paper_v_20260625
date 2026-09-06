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
    KernelInvocationCensusV5, execute_prediction_cell_v5,
    execute_prediction_schedule_v5, validate_release_execution_kernel_v5,
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
            "executable_version": "DG05_EXECUTABLE_V5",
            "historical_execution_kernel_hash": self.executor.executable_manifest_hash,
            "predecessor_v4_manifest_hash": H,
            "implementation_authorities": [], "nested_authority_hashes": {},
            "transitive_implementation_authority": {"self_hash": H},
            "readiness": "READY_FOR_USER_REAPPROVAL", "source_commit": G,
        })
        self.initialized = self_hashed({
            "schema": "dg05_production_chain_state_v2",
            "state": "PREACCESS_FROZEN_KERNEL_RELEASE_INITIALIZED",
            "release_manifest_hash": self.release["self_hash"],
            "predecessor_v4_manifest_hash": H,
            "authority_mode": "PREACCESS_FROZEN_KERNEL_REHEARSAL",
            "data_access_mode": "SYNTHETIC_ONLY_NO_PROTECTED_DISCOVERY",
            "protected_access_authorized": False,
            "execution_kernel_identity": "FROZEN_PRODUCTION_SCIENTIFIC_KERNEL_V1",
            "implementation_authority_hash": digest([]),
            "nested_authority_hash": digest({}),
            "transitive_implementation_authority_hash": H,
            "attack_test_accesses": 0, "label_scenario_accesses": 0,
        })

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
        object.__setattr__(executor, "executable_manifest_hash", self.release["historical_execution_kernel_hash"])
        production = self_hashed({
            "schema": "dg05_production_chain_state_v2",
            "state": "APPROVED_PRODUCTION_RELEASE_INITIALIZED",
            "release_manifest_hash": self.release["self_hash"],
            "predecessor_v4_manifest_hash": H,
            "authority_mode": "PRODUCTION",
            "data_access_mode": "PROTECTED_DATA_ACCESS_REQUIRES_EXACT_USER_APPROVAL",
            "protected_access_authorized": True,
            "execution_kernel_identity": "FROZEN_PRODUCTION_SCIENTIFIC_KERNEL_V1",
            "implementation_authority_hash": digest([]),
            "nested_authority_hash": digest({}),
            "transitive_implementation_authority_hash": H,
            "attack_test_accesses": 0, "label_scenario_accesses": 0,
        })
        with patch.object(DG05ProductionExecutorV1, "validate", autospec=True) as validate:
            validate_release_execution_kernel_v5(
                release=self.release, predecessor_v3=self.predecessor,
                initialized_release_state=production, executor=executor)
        validate.assert_called_once_with(executor)

    def test_route_rejects_transitive_implementation_state_disconnect(self) -> None:
        bad = self_hashed({
            **{key: value for key, value in self.initialized.items() if key != "self_hash"},
            "transitive_implementation_authority_hash": "c" * 64,
        })
        with self.assertRaisesRegex(ValueError, "V5_RELEASE_KERNEL_BINDING_MISMATCH"):
            validate_release_execution_kernel_v5(
                release=self.release,
                predecessor_v3=self.predecessor,
                initialized_release_state=bad,
                executor=self.executor,
            )

    def test_handcrafted_unhashed_production_state_is_rejected(self) -> None:
        executor = object.__new__(DG05ProductionExecutorV1)
        object.__setattr__(executor, "authority_mode", "PRODUCTION")
        object.__setattr__(executor, "executable_manifest_hash", self.release["historical_execution_kernel_hash"])
        handcrafted = {
            "release_manifest_hash": self.release["self_hash"],
            "authority_mode": "PRODUCTION",
            "data_access_mode": "PROTECTED_DATA_ACCESS_REQUIRES_EXACT_USER_APPROVAL",
            "protected_access_authorized": True,
            "execution_kernel_identity": "FROZEN_PRODUCTION_SCIENTIFIC_KERNEL_V1",
        }
        with self.assertRaisesRegex(ValueError, "V5_RELEASE_KERNEL_BINDING_MISMATCH"):
            validate_release_execution_kernel_v5(
                release=self.release, predecessor_v3=self.predecessor,
                initialized_release_state=handcrafted, executor=executor)

    def test_timestamp_authority_disconnect_fails_before_kernel(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            times = [(datetime(2026, 1, 1) + timedelta(seconds=i)).isoformat() for i in range(2)]
            cell, projection, timestamp, path = self._fixture(root, times)
            bad_timestamp = type(timestamp)(
                **{**timestamp.__dict__, "timestamp_vector_hash": "c" * 64}
            )
            with (
                patch("paperworks.validation_v2.dg05_production_route_v5.validate_release_execution_kernel_v5"),
                patch("paperworks.validation_v2.dg05_production_route_v5.execute_normal_method_v4") as kernel,
                self.assertRaisesRegex(ValueError, "PROJECTION_TIMESTAMP_AUTHORITY_BINDING_MISMATCH"),
            ):
                execute_prediction_cell_v5(
                    cell=cell, dispatch=self.dispatch, projection=projection, timestamp=bad_timestamp,
                    release=self.release, predecessor_v3=self.predecessor,
                    initialized_release_state=self.initialized, executor=self.executor,
                    projection_path=path, output_directory=root / "out", source_commit=G,
                    repository_root=Path.cwd(), invocation_census=KernelInvocationCensusV5())
            kernel.assert_not_called()

    def test_schedule_rejects_reorder_duplicate_and_dispatch_swap(self) -> None:
        first = {"cell_id": "1", "panel_id": "P", "file_id": "F", "method_id": "M",
                 "dispatch_authority_hash": H}
        second = {**first, "cell_id": "2", "method_id": "N"}
        expected = self_hashed({
            "schema": "expected_prediction_cell_census_builder_v1",
            "physical_file_authority_hash": H,
            "dispatch_registry_hash": H,
            "cells": [first, second],
            "count": 2,
        })
        mutations = [
            self_hashed({**{k: v for k, v in expected.items() if k not in {"self_hash", "cells"}},
                         "cells": [second, first]}),
            self_hashed({**{k: v for k, v in expected.items() if k not in {"self_hash", "cells"}},
                         "cells": [first, first]}),
            self_hashed({**{k: v for k, v in expected.items() if k not in {"self_hash", "dispatch_registry_hash"}},
                         "dispatch_registry_hash": "c" * 64}),
        ]
        for mutation in mutations:
            with (
                self.subTest(mutation=mutation),
                patch(
                    "paperworks.validation_v2.dg05_production_route_v5."
                    "build_expected_prediction_cell_census_v1",
                    return_value=expected,
                ),
                self.assertRaisesRegex(ValueError, "PREDICTION_CELL_CENSUS_ROOT_REPLAY_FAILED"),
            ):
                execute_prediction_schedule_v5(
                    census=mutation,
                    physical=object(),
                    dispatch=self.dispatch,
                    projections={},
                    timestamps={},
                    release=self.release,
                    predecessor_v3=self.predecessor,
                    initialized_release_state=self.initialized,
                    executor=self.executor,
                    output_directory=Path("unused"),
                    source_commit=G,
                    repository_root=Path.cwd(),
                )


if __name__ == "__main__":
    unittest.main()
