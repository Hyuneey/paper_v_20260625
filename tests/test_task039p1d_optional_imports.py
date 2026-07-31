from __future__ import annotations

import ast
import importlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Task039P1DOptionalImportTests(unittest.TestCase):
    def test_lightweight_packages_import_without_loading_torch(self) -> None:
        import paperworks
        import paperworks.candidates
        import paperworks.e2e
        import paperworks.gdn
        from paperworks.gdn import (
            GDNExtractionConfig,
            GDNExtractionError,
            cosine_similarity_matrix,
            extract_masked_topk_edges,
        )

        self.assertIsNotNone(paperworks)
        self.assertIsNotNone(GDNExtractionConfig)
        self.assertIsNotNone(GDNExtractionError)
        self.assertTrue(callable(cosine_similarity_matrix))
        self.assertTrue(callable(extract_masked_topk_edges))
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("torch_geometric", sys.modules)
        self.assertNotIn("paperworks.gdn.torch_backend", sys.modules)
        self.assertNotIn("paperworks.candidates.smoke", sys.modules)

    def test_optional_public_symbols_fail_through_project_error(self) -> None:
        import paperworks.gdn as gdn

        status = gdn.inspect_gdn_dependencies()
        self.assertFalse(status.backend_importable)
        for name in (
            "TorchGDNEmbeddingModel",
            "TorchGDNTrainingConfig",
            "fit_torch_gdn_embedding_checkpoint",
        ):
            with self.subTest(name=name):
                with self.assertRaises(gdn.GDNOptionalDependencyError) as ctx:
                    getattr(gdn, name)
                self.assertEqual(
                    ctx.exception.issue_code,
                    "GDN_OPTIONAL_DEPENDENCY_UNAVAILABLE",
                )

    def test_direct_torch_backend_import_uses_project_error(self) -> None:
        from paperworks.gdn import GDNOptionalDependencyError

        with self.assertRaises(GDNOptionalDependencyError):
            importlib.import_module("paperworks.gdn.torch_backend")

    def test_public_initializers_have_no_direct_heavy_import(self) -> None:
        for relative in (
            "src/paperworks/__init__.py",
            "src/paperworks/gdn/__init__.py",
            "src/paperworks/candidates/__init__.py",
            "src/paperworks/e2e/__init__.py",
        ):
            tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
            self.assertFalse(
                any(
                    name == "torch"
                    or name.startswith("torch.")
                    or name == "torch_geometric"
                    or name.startswith("torch_geometric.")
                    for name in imports
                ),
                relative,
            )


if __name__ == "__main__":
    unittest.main()
