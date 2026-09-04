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

    def test_current_state_contract_and_scientific_safety_counters(self) -> None:
        data = load_registry(RCC_ROOT)
        result = validator.ValidationResult()
        validator._validate_authority(data, result)
        self.assertEqual([], result.errors)
        self.assertEqual(3, len(data["state"]["top_user_todo"]))
        self.assertEqual(8, len(data["state"]["user_todo_items"]))
        self.assertEqual(32, len(data["components"]))
        self.assertEqual(11, len(data["experiments"]))
        self.assertEqual(15, len(data["claims"]))
        self.assertEqual(19, len(data["risks"]))
        self.assertEqual(43, len(data["artifacts"]))
        self.assertEqual(
            {
                "scientific_executions": 4,
                "test2_feature_accesses": 0,
                "test2_label_accesses": 0,
                "new_private_exposures": 0,
            },
            data["state"]["safety_counters"],
        )

    def test_status_semantics_separate_review_integrity_reproduction_and_validation(self) -> None:
        state = load_registry(RCC_ROOT)["state"]
        semantics = state["status_semantics"]
        self.assertIn("source or evidence status", semantics["audited_field"])
        self.assertIn("not a performance-validation flag", semantics["audited_field"])
        self.assertIn("explicit result-specific integrity artifacts", semantics["result_integrity_audit"])
        self.assertIn("independent reproduction", semantics["reproduced_field"])
        self.assertIn("claims.csv", semantics["scientific_validation"])
        self.assertIn("narrow implementation or contract claim", semantics["claim_ready_field"])

    def test_every_scientific_source_commit_is_explicitly_allowlisted(self) -> None:
        data = load_registry(RCC_ROOT)
        allowed = {
            "codex/exp03b-provider-exec-001": {"811d5817bed1484bb3d0c36704bd74f224f4c526"},
            "codex/exp03b-payload-reduce-001": {"6b8463f5e420485fca0848d315db8cb7af112117"},
            "validation-v2-exp03b-prep-001": {"ca78664d03464b81f56cf42c169c24f1153e69c9"},
            "validation-v2-exp03-provider-exec-001": {"9e0c669d5efa03afcd13342fa1fc3dbc8ba8f3f4"},
            "validation-v2-gdn-front-exp04-001": {"94ae44dac900cce75ed83ee2801be38750afed4a"},
            "origin/research-v6-thesis-checkpoint": {AUTHORITY_COMMIT},
            "validation-v2-core-exp02": {"9cb47e0efb868048d4a523ec4cfaca53bd342ab7"},
            "validation-v2-exp01b-gdn-xai": {
                "9e2aad7ded63238f6300f282d0841671c7c14ce0",
                "e0a14ab61762f7e7ce8319d58643dc483dda6a02",
            },
            "validation-v2": {"7125c038817a6ac9ee4392748de802e2069b44f6e"},
            "validation-v2-eval-expansion-001": {
                "07ed817cd809762a93a910cb10dc14c1d4b91c1f",
                "d1489b67618b1e307a31a15ccb27d6dad57795c4",
            },
        }
        for name in ("experiments", "claims", "risks"):
            for row in data[name]:
                self.assertIn(row["scientific_source_commit"], allowed[row["scientific_source_ref"]])
        self.assertEqual(
            {validator.OVERLAY_COMMIT},
            {row["scientific_source_commit"] for row in data["components"] if row["component_id"] == "THESIS_DRAFT"},
        )
        self.assertEqual(
            {AUTHORITY_COMMIT},
            {row["scientific_source_commit"] for row in data["components"] if row["component_id"] != "THESIS_DRAFT"},
        )
        allowed_history_commits = {
            "9e0c669d5efa03afcd13342fa1fc3dbc8ba8f3f4",
            AUTHORITY_COMMIT,
            "NONE",
            "e81baadcfd6cf6b9f23d307056455e024876c2ed",
            "9cb47e0efb868048d4a523ec4cfaca53bd342ab7",
            "e0a14ab61762f7e7ce8319d58643dc483dda6a02",
            "94ae44dac900cce75ed83ee2801be38750afed4a",
            "07ed817cd809762a93a910cb10dc14c1d4b91c1f",
            "d1489b67618b1e307a31a15ccb27d6dad57795c4",
        }
        for name in ("decisions", "timeline"):
            self.assertLessEqual({row["source_commit"] for row in data[name]}, allowed_history_commits)
            for row in data[name]:
                if row["source"] == "USER_CONTEXT":
                    self.assertEqual("NONE", row["source_commit"])
        self.assertEqual(
            {validator.OVERLAY_COMMIT},
            {row["source_commit"] for row in data["artifacts"] if row["artifact_id"] == "ART-THESIS-DRAFT"},
        )

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

    def test_no_stale_seed_identifiers_remain(self) -> None:
        data = load_registry(RCC_ROOT)
        self.assertNotIn("EXP-GDN-CONTRIBUTION", {row["experiment_id"] for row in data["experiments"]})
        self.assertNotIn("CLAIM-ARCH-IMPLEMENTED", {row["claim_id"] for row in data["claims"]})
        self.assertEqual(
            {f"EXP-{index:02d}" for index in range(1, 7)}
            | {"EXP-01B", "EXP-03B", "EXP-H23-HOLDOUT", "EXP-H22-XVER", "EXP-H21-XVER"},
            {row["experiment_id"] for row in data["experiments"]},
        )
        self.assertEqual({f"CLAIM-{letter}" for letter in "ABCDEFGHIJKLMN"}|{'CLAIM-EXP03B-PREP'}, {row["claim_id"] for row in data["claims"]})

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

    def test_history_counts_precision_and_cross_references(self) -> None:
        data = load_registry(RCC_ROOT)
        self.assertEqual(34, len(data["timeline"]))
        self.assertEqual(24, len(data["decisions"]))
        self.assertEqual(1, len(data["history"]["confirmation_questions"]))
        result = validator.ValidationResult()
        validator._validate_dates(data, result)
        validator._validate_references(data, result)
        validator._validate_history(data, result, RCC_ROOT.parent, True)
        self.assertEqual([], result.errors)

    def test_user_context_does_not_claim_false_precision_or_git_authority(self) -> None:
        data = load_registry(RCC_ROOT)
        early = [row for row in data["timeline"] if row["event_id"] in {"EVENT-001", "EVENT-002", "EVENT-003", "EVENT-004"}]
        self.assertTrue(all(row["date_precision"] in {"MONTH", "RANGE"} for row in early))
        self.assertTrue(all(row["source"] in {"USER_CONTEXT", "USER_CONFIRMED_CONTEXT"} for row in early))
        self.assertTrue(all(row["source_commit"] == "NONE" for row in early))
        decisions = {row["decision_id"]: row for row in data["decisions"]}
        for decision_id in ("DEC-003", "DEC-005", "DEC-015", "DEC-019"):
            self.assertEqual("true", decisions[decision_id]["user_approved"])
        self.assertEqual("true", decisions["DEC-009"]["user_approved"])
        self.assertEqual("HIGH", decisions["DEC-009"]["confidence"])

    def test_history_cannot_promote_current_claims(self) -> None:
        data = load_registry(RCC_ROOT)
        claim_status = {row["claim_id"]: row["status"] for row in data["claims"]}
        self.assertEqual("DEVELOPMENT_NOT_SUPPORTED", claim_status["CLAIM-E"])
        self.assertEqual("NOT_SUPPORTED", claim_status["CLAIM-F"])
        self.assertEqual("DEVELOPMENT_NOT_SUPPORTED", claim_status["CLAIM-I"])
        self.assertEqual("NOT_SUPPORTED", claim_status["CLAIM-J"])

    def test_august_feedback_temporal_corrections_are_explicit(self) -> None:
        lineage = {row["date"]: row for row in load_registry(RCC_ROOT)["history"]["professor_feedback_lineage"]}
        self.assertTrue(lineage["2026-08-18"]["classification"].endswith("NOT_PROFESSOR_FEEDBACK"))
        self.assertTrue(lineage["2026-08-26"]["classification"].endswith("NOT_PROFESSOR_FEEDBACK"))
        self.assertIn("reinforced", lineage["2026-08-04"]["interpretation"])

    def test_arch000_component_map_and_deep_review_parts(self) -> None:
        data = load_registry(RCC_ROOT)
        self.assertEqual(32, len(data["components"]))
        self.assertEqual({f"ARCH-{index:03d}" for index in range(1, 12)}, {row["deep_review_part"] for row in data["components"]})
        self.assertEqual(11, len(data["architecture_details"]))
        self.assertEqual("DG-04 — EXP-03B 이후 최종 제목·Agentic 기여 결정" if data['state'].get('exp03b_execution') else "DG-03B_REVISED — EXP-03B Provider Execution Decision (DG-04 DEFERRED_UNTIL_EXP03B)", data["state"]["exact_next_task"])

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
