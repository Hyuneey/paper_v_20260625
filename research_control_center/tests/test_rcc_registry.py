from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path


RCC_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = RCC_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_registry as validator  # noqa: E402
from build_dashboard import AUTHORITY_COMMIT, load_registry  # noqa: E402


class RegistryValidationTests(unittest.TestCase):
    def test_frozen_registry_contract_passes(self) -> None:
        result = validator.validate_registry(RCC_ROOT, check_outputs=False)
        self.assertEqual([], result.errors)

    def test_all_required_headers_are_exact(self) -> None:
        for name, expected in validator.EXPECTED_HEADERS.items():
            actual = validator._read_header(RCC_ROOT / "registry" / f"{name}.csv")
            self.assertEqual(expected, actual)

    def test_duplicate_component_id_is_rejected(self) -> None:
        data = load_registry(RCC_ROOT)
        data["components"].append(dict(data["components"][0]))
        result = validator.ValidationResult()
        validator._validate_unique_ids(data, result)
        self.assertIn("components.component_id contains duplicates", result.errors)

    def test_authority_mutation_is_rejected(self) -> None:
        data = copy.deepcopy(load_registry(RCC_ROOT))
        data["state"]["scientific_authority"]["commit"] = "0" * 40
        result = validator.ValidationResult()
        validator._validate_authority(data, result)
        self.assertTrue(any("scientific authority" in error for error in result.errors))

    def test_current_state_contract_and_zero_safety_counters(self) -> None:
        data = load_registry(RCC_ROOT)
        result = validator.ValidationResult()
        validator._validate_authority(data, result)
        self.assertEqual([], result.errors)
        self.assertEqual(3, len(data["state"]["top_user_todo"]))
        self.assertEqual(
            {
                "scientific_executions": 0,
                "test2_feature_accesses": 0,
                "test2_label_accesses": 0,
                "new_private_exposures": 0,
            },
            data["state"]["safety_counters"],
        )

    def test_every_scientific_source_commit_is_pinned(self) -> None:
        data = load_registry(RCC_ROOT)
        for name in ("components", "experiments", "claims", "risks"):
            self.assertEqual({AUTHORITY_COMMIT}, {row["scientific_source_commit"] for row in data[name]})
        for name in ("artifacts", "decisions", "timeline"):
            self.assertEqual({AUTHORITY_COMMIT}, {row["source_commit"] for row in data[name]})

    def test_path_safety_accepts_only_repository_relative_posix_paths(self) -> None:
        self.assertTrue(validator.is_safe_relative_path("docs/report.md"))
        self.assertFalse(validator.is_safe_relative_path("../docs/report.md"))
        self.assertFalse(validator.is_safe_relative_path("/docs/report.md"))
        self.assertFalse(validator.is_safe_relative_path("docs\\report.md"))
        self.assertFalse(validator.is_safe_relative_path("X" + ":\\private\\report.md"))

    def test_registry_paths_resolve_in_pinned_git_tree(self) -> None:
        data = load_registry(RCC_ROOT)
        result = validator.ValidationResult()
        validator._validate_paths(data, result, RCC_ROOT.parent, True)
        self.assertEqual([], result.errors)

    def test_local_authority_refs_resolve_to_exact_pins(self) -> None:
        result = validator.ValidationResult()
        validator._validate_git_authorities(RCC_ROOT.parent, result)
        self.assertEqual([], result.errors)

    def test_current_and_superseded_artifact_is_rejected(self) -> None:
        data = copy.deepcopy(load_registry(RCC_ROOT))
        data["artifacts"][0]["superseded"] = "true"
        result = validator.ValidationResult()
        validator._validate_enums(data, result)
        self.assertTrue(any("current and superseded" in error for error in result.errors))

    def test_invalid_timeline_event_type_is_rejected(self) -> None:
        data = copy.deepcopy(load_registry(RCC_ROOT))
        data["timeline"][0]["event_type"] = "RESULT_INTERPRETATION"
        result = validator.ValidationResult()
        validator._validate_enums(data, result)
        self.assertTrue(any("event_type" in error for error in result.errors))

    def test_bootstrap_is_excluded_from_new_file_privacy_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "bootstrap" / "RCC_000"
            legacy.mkdir(parents=True)
            (legacy / "preserved.md").write_text("X" + ":\\legacy\\locator", encoding="utf-8")
            (root / "safe.md").write_text("public-safe metadata", encoding="utf-8")
            self.assertEqual([], validator.privacy_exposures(root))

    def test_new_absolute_locator_is_reported_without_echoing_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "unsafe.md").write_text("X" + ":\\private\\locator", encoding="utf-8")
            self.assertEqual(["unsafe.md"], validator.privacy_exposures(root))


if __name__ == "__main__":
    unittest.main()
