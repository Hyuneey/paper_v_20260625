from __future__ import annotations

import sys
import unittest

from paperworks.gdn.dependencies import (
    GDNDependencyStatusV1,
    inspect_gdn_dependencies,
)


class Task039P1DDependencyStatusTests(unittest.TestCase):
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
