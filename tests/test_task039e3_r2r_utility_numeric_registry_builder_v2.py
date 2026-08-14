from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.build_task039e3_r2r_utility_numeric_registry_v2 import (
    _absolute_file,
    _new_output,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_task039e3_r2r_utility_numeric_registry_v2.py"


class PrivateNumericRegistryBuilderV2Tests(unittest.TestCase):
    def test_inputs_and_output_are_explicit_absolute_paths(self) -> None:
        with self.assertRaises(ValueError):
            _absolute_file("relative.json", "ledger")
        with self.assertRaises(ValueError):
            _new_output("relative.json")

    def test_private_output_inside_git_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            with self.assertRaises(ValueError):
                _new_output(str(Path(directory) / "private-registry.json"))

    def test_builder_has_no_discovery_or_default_input(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for prohibited in ("rglob(", ".glob(", "os.walk", "TASK039E1_PRIVATE_ROOT"):
            self.assertNotIn(prohibited, source)
        self.assertIn('parser.add_argument("--e1-private-ledger", required=True)', source)
        self.assertIn('parser.add_argument("--output-private-registry", required=True)', source)


if __name__ == "__main__":
    unittest.main()
