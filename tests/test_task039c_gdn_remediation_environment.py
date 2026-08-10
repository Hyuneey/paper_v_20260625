from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from paperworks.gdn.gdn_remediation_environment_v1 import (
    DETERMINISTIC_ENVIRONMENT,
    ExactGDNEnvironmentUnavailable,
    ExternalRemediationRootsV1,
    FIDELITY_RECEIPT_HASH,
    GDNRResultContractError,
    MissingUnapprovedExtensionError,
    REQUIRED_PLATFORM_ID,
    REQUIRED_PYTHON_VERSION,
    REQUIRED_TOP_LEVEL_PACKAGES,
    REQUIRED_TOP_LEVEL_WHEELS,
    TASK039CGDNEnvironmentReceiptV1,
    WheelRecordV1,
    assert_public_payload_sanitized_v1,
    build_sanitized_wheelhouse_receipt_v1,
    inspect_wheelhouse_v1,
)
from paperworks.v6.common import stable_hash_v1


HASH = "a" * 64


def exact_records() -> tuple[WheelRecordV1, ...]:
    torch_name, torch_hash = REQUIRED_TOP_LEVEL_WHEELS["torch"]
    pyg_name, pyg_hash = REQUIRED_TOP_LEVEL_WHEELS["torch-geometric"]
    return (
        WheelRecordV1(
            "jsonschema-4.26.0-py3-none-any.whl",
            "jsonschema",
            "4.26.0",
            100,
            "1" * 64,
        ),
        WheelRecordV1(torch_name, "torch", "2.12.1", 200, torch_hash),
        WheelRecordV1(
            pyg_name,
            "torch-geometric",
            "2.8.0",
            300,
            pyg_hash,
        ),
    )


def environment_receipt(**changes) -> TASK039CGDNEnvironmentReceiptV1:
    records = exact_records()
    wheelhouse = build_sanitized_wheelhouse_receipt_v1(
        records, created_at="2026-08-10T00:00:00+00:00"
    )
    values = {
        "python_version": REQUIRED_PYTHON_VERSION,
        "platform_id": REQUIRED_PLATFORM_ID,
        "top_level_packages": REQUIRED_TOP_LEVEL_PACKAGES,
        "wheel_manifest": records,
        "sanitized_wheel_manifest_hash": wheelhouse[
            "sanitized_wheel_manifest_hash"
        ],
        "wheelhouse_receipt_hash": wheelhouse["artifact_hash"],
        "installed_package_freeze_hash": "2" * 64,
        "installed_package_count": 4,
        "pip_version": "26.0",
        "pip_check_status": "passed",
        "dependency_environment_fingerprint": "3" * 64,
        "fidelity_receipt_hash": FIDELITY_RECEIPT_HASH,
        "torch_runtime_version": "2.12.1+cpu",
        "cpu_execution_available": True,
        "created_at": "2026-08-10T00:00:00+00:00",
    }
    values.update(changes)
    return TASK039CGDNEnvironmentReceiptV1(**values)


class Task039CGDNRemediationEnvironmentTests(unittest.TestCase):
    def test_exact_python_platform_torch_and_pyg_are_accepted(self) -> None:
        receipt = environment_receipt()
        payload = receipt.to_dict()
        observed = payload.pop("artifact_hash")
        self.assertEqual(stable_hash_v1(payload), observed)
        self.assertEqual(payload["python_version"], "3.12.13")
        self.assertEqual(payload["top_level_packages"]["torch"], "2.12.1")
        self.assertEqual(
            payload["top_level_packages"]["torch-geometric"], "2.8.0"
        )
        self.assertEqual(payload["deterministic_environment"], DETERMINISTIC_ENVIRONMENT)

    def test_wrong_python_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ExactGDNEnvironmentUnavailable, "not exact"):
            environment_receipt(python_version="3.12.12")

    def test_wrong_torch_version_is_rejected(self) -> None:
        packages = dict(REQUIRED_TOP_LEVEL_PACKAGES)
        packages["torch"] = "2.11.0"
        with self.assertRaisesRegex(ExactGDNEnvironmentUnavailable, "not exact"):
            environment_receipt(top_level_packages=packages)

    def test_wrong_pyg_and_post1_versions_are_rejected(self) -> None:
        for version in ("2.7.0", "2.8.0.post1"):
            with self.subTest(version=version):
                packages = dict(REQUIRED_TOP_LEVEL_PACKAGES)
                packages["torch-geometric"] = version
                with self.assertRaisesRegex(
                    ExactGDNEnvironmentUnavailable, "not exact"
                ):
                    environment_receipt(top_level_packages=packages)

    def test_top_level_frozen_wheel_hashes_are_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = exact_records()
            by_file = {record.file_name: record for record in records}
            for name in by_file:
                (root / name).write_bytes(b"synthetic")
            with patch.object(
                WheelRecordV1,
                "from_path",
                side_effect=lambda path: by_file[path.name],
            ):
                self.assertEqual(inspect_wheelhouse_v1(root), records)

    def test_frozen_wheel_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = list(exact_records())
            torch = records[1]
            records[1] = WheelRecordV1(
                torch.file_name,
                torch.package_name,
                torch.version,
                torch.byte_size,
                "0" * 64,
            )
            by_file = {record.file_name: record for record in records}
            for name in by_file:
                (root / name).write_bytes(b"synthetic")
            with patch.object(
                WheelRecordV1,
                "from_path",
                side_effect=lambda path: by_file[path.name],
            ):
                with self.assertRaisesRegex(
                    ExactGDNEnvironmentUnavailable, "identity mismatch"
                ):
                    inspect_wheelhouse_v1(root)

    def test_source_distribution_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "torch-2.12.1.tar.gz").write_bytes(b"synthetic")
            with self.assertRaisesRegex(
                ExactGDNEnvironmentUnavailable, "non-wheel"
            ):
                inspect_wheelhouse_v1(root)

    def test_unapproved_pyg_extension_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = exact_records() + (
                WheelRecordV1(
                    "torch_scatter-2.1.2-py3-none-any.whl",
                    "torch-scatter",
                    "2.1.2",
                    10,
                    "4" * 64,
                ),
            )
            by_file = {record.file_name: record for record in records}
            for name in by_file:
                (root / name).write_bytes(b"synthetic")
            with patch.object(
                WheelRecordV1,
                "from_path",
                side_effect=lambda path: by_file[path.name],
            ):
                with self.assertRaises(MissingUnapprovedExtensionError):
                    inspect_wheelhouse_v1(root)

    def test_environment_root_inside_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / "repository"
            repository.mkdir()
            environment = {
                "TASK039C_GDN_ENV_ROOT": str(repository / "env"),
                "TASK039C_GDN_WHEELHOUSE": str(base / "wheelhouse"),
                "TASK039C_GDN_PRIVATE_ROOT": str(base / "private"),
                "HAI_DATA_ROOT": str(base / "hai"),
            }
            with self.assertRaisesRegex(
                ExactGDNEnvironmentUnavailable, "outside Git"
            ):
                ExternalRemediationRootsV1.from_environment(
                    repository_root=repository,
                    environ=environment,
                )

    def test_distinct_external_roots_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / "repository"
            repository.mkdir()
            environment = {
                "TASK039C_GDN_ENV_ROOT": str(base / "env"),
                "TASK039C_GDN_WHEELHOUSE": str(base / "wheelhouse"),
                "TASK039C_GDN_PRIVATE_ROOT": str(base / "private"),
                "HAI_DATA_ROOT": str(base / "hai"),
            }
            roots = ExternalRemediationRootsV1.from_environment(
                repository_root=repository,
                environ=environment,
            )
            self.assertEqual(len(set(roots.to_private_dict().values())), 4)

    def test_public_absolute_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(GDNRResultContractError, "private path"):
            assert_public_payload_sanitized_v1(
                {"environment": r"C:\Users\researcher\private-env"}
            )

    def test_fidelity_receipt_binding_is_exact(self) -> None:
        with self.assertRaisesRegex(Exception, "fidelity"):
            environment_receipt(fidelity_receipt_hash=HASH)


if __name__ == "__main__":
    unittest.main()
