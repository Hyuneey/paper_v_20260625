from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.dg05_implementation_closure_v1 import (
    DG05ImplementationClosureV1Error,
    build_transitive_implementation_authority_v1,
    replay_transitive_implementation_authority_v1,
    repository_python_import_closure_v1,
)


class ImplementationClosureV1Tests(unittest.TestCase):
    def _repo(self, root: Path) -> Path:
        for relative, content in {
            "src/paperworks/__init__.py": "from . import a\n",
            "src/paperworks/a.py": "from .b import value\n",
            "src/paperworks/b.py": "from paperworks import c\nvalue = c.VALUE\n",
            "src/paperworks/c.py": "VALUE = 1\n",
            "scripts/entry.py": "from paperworks.a import value\n",
        }.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root / "scripts/entry.py"

    def test_fixed_point_includes_relative_transitive_and_package_initializers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            entry = self._repo(root)
            closure = repository_python_import_closure_v1(
                repository_root=root, root_paths=[entry]
            )
            self.assertEqual(
                {path.relative_to(root).as_posix() for path in closure},
                {
                    "scripts/entry.py",
                    "src/paperworks/__init__.py",
                    "src/paperworks/a.py",
                    "src/paperworks/b.py",
                    "src/paperworks/c.py",
                },
            )

    def test_replay_rejects_transitive_byte_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            entry = self._repo(root)
            authority = build_transitive_implementation_authority_v1(
                repository_root=root,
                root_paths=[entry],
                source_commit="a" * 40,
            )
            (root / "src/paperworks/c.py").write_text("VALUE = 2\n", encoding="utf-8")
            with self.assertRaisesRegex(
                DG05ImplementationClosureV1Error,
                "TRANSITIVE_IMPLEMENTATION_CLOSURE_REPLAY_FAILED",
            ):
                replay_transitive_implementation_authority_v1(
                    repository_root=root,
                    authority=authority,
                    expected_root_paths=[entry],
                )


if __name__ == "__main__":
    unittest.main()
