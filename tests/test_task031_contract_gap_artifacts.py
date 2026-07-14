from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class Task031ContractGapArtifactTests(unittest.TestCase):
    def test_required_outputs_exist(self) -> None:
        paths = [
            "docs/method/CONTRACT_TO_CODE_GAP_MATRIX.md",
            "docs/method/LEGACY_TO_V1_ARTIFACT_CROSSWALK.md",
            "docs/method/MVP_DELAYED_RESPONSE_VERTICAL_SLICE.md",
            "docs/method/SCHEMA_VALIDATION_STRATEGY.md",
            "docs/method/VERIFIER_STAGE_IMPLEMENTATION_MAP.md",
            "docs/method/RUNTIME_AND_EXPLANATION_MIGRATION_MAP.md",
            "docs/method/IMPLEMENTATION_SEQUENCE_AFTER_TASK030.md",
            "configs/method/task031_mvp_scope.json",
            "docs/task_reports/TASK-031_SOURCE_INVENTORY.json",
            "docs/task_reports/TASK-031_GAP_AUDIT_REPORT.json",
            "docs/task_reports/TASK-031_REPORT.md",
            "TASKS/TASK-031_CONTRACT_TO_CODE_GAP_AUDIT.md",
        ]
        for relative in paths:
            self.assertTrue((REPO_ROOT / relative).is_file(), relative)

    def test_scope_and_compatibility_are_frozen(self) -> None:
        config = json.loads(
            (REPO_ROOT / "configs/method/task031_mvp_scope.json").read_text(encoding="utf-8")
        )
        self.assertEqual(config["mvp"]["relation_family"], "delayed_response")
        self.assertEqual(config["mvp"]["source_cardinality"], 1)
        self.assertEqual(config["mvp"]["target_cardinality"], 1)
        self.assertFalse(config["version_policy"]["automatic_silent_conversion"])
        self.assertTrue(config["version_policy"]["source_and_target_hashes_required"])
        self.assertFalse(config["next_task"]["automatically_authorized"])
        self.assertFalse(config["boundaries"]["src_paperworks_changes"])
        self.assertFalse(config["boundaries"]["dependency_changes"])

    def test_inventory_has_required_fields_for_every_public_symbol(self) -> None:
        inventory = json.loads(
            (REPO_ROOT / "docs/task_reports/TASK-031_SOURCE_INVENTORY.json").read_text(encoding="utf-8")
        )
        self.assertEqual(inventory["inventory_method"], "python_ast_and_source_text_only")
        self.assertGreater(inventory["public_symbol_count"], 100)
        self.assertGreater(inventory["artifact_type_count"], 10)
        required = {
            "symbol",
            "module",
            "current_role",
            "input_contract",
            "output_contract",
            "dependencies",
            "split_assumptions",
            "numeric_authority",
            "runtime_behavior",
            "test_coverage",
            "known_limitations",
        }
        for item in inventory["public_symbols"]:
            self.assertTrue(required.issubset(item), item.get("symbol"))

    def test_documents_do_not_overstate_fixture_validator(self) -> None:
        strategy = (REPO_ROOT / "docs/method/SCHEMA_VALIDATION_STRATEGY.md").read_text(encoding="utf-8")
        self.assertIn("not a complete Draft 2020-12 implementation", strategy)
        self.assertIn("Draft202012Validator", strategy)
        self.assertIn("not declared", strategy)

    def test_gap_report_preserves_claim_boundaries(self) -> None:
        report = json.loads(
            (REPO_ROOT / "docs/task_reports/TASK-031_GAP_AUDIT_REPORT.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["claim_status"], "migration_planning_only")
        self.assertFalse(report["boundaries_observed"]["datasets_accessed"])
        self.assertFalse(report["boundaries_observed"]["provider_calls"])
        self.assertFalse(report["boundaries_observed"]["generated_code_loaded_or_executed"])
        self.assertTrue(report["silent_conversion_prohibited"])
        self.assertTrue(report["synthetic_smoke_parameter_promotion_prohibited"])


if __name__ == "__main__":
    unittest.main()
