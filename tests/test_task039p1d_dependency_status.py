from __future__ import annotations

import sys
import unittest

from paperworks.gdn.upstream_candidate_backend_v1 import DependencyEnvironmentV1
from paperworks.gdn.dependencies import (
    GDNDependencyStatusV1,
    inspect_gdn_dependencies,
)


class Task039P1DDependencyStatusTests(unittest.TestCase):
    def test_official_torch_local_build_tag_preserves_exact_release_gate(self) -> None:
        for version in ("2.12.1+cpu", "2.12.1+cu130"):
            environment = DependencyEnvironmentV1(
                environment_id="synthetic",
                python_version="3.12.13",
                platform_id="windows-amd64",
                torch_version=version,
                torch_geometric_version="2.8.0",
            )
            self.assertTrue(environment.exact_approved_backend)
        wrong_release = DependencyEnvironmentV1(
            environment_id="synthetic",
            python_version="3.12.13",
            platform_id="windows-amd64",
            torch_version="2.12.2+cu130",
            torch_geometric_version="2.8.0",
        )
        self.assertFalse(wrong_release.exact_approved_backend)

    def test_inspection_is_deterministic_and_does_not_import_backend(self) -> None:
        before = set(sys.modules)
        first = inspect_gdn_dependencies()
        second = inspect_gdn_dependencies()
        self.assertEqual(first, second)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertNotIn("torch", set(sys.modules) - before)
        self.assertNotIn("torch_geometric", set(sys.modules) - before)
        self.assertEqual(len(first.artifact_hash), 64)

    def test_status_fails_on_inconsistent_availability(self) -> None:
        with self.assertRaises(ValueError):
            GDNDependencyStatusV1(
                torch_available=False,
                torch_geometric_available=False,
                torch_version="2.12.1",
                torch_geometric_version=None,
                backend_importable=False,
                missing_packages=("torch", "torch-geometric"),
            )
        with self.assertRaises(ValueError):
            GDNDependencyStatusV1(
                torch_available=True,
                torch_geometric_available=True,
                torch_version="2.12.1",
                torch_geometric_version="2.8.0",
                backend_importable=False,
                missing_packages=(),
            )


if __name__ == "__main__":
    unittest.main()
