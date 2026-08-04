from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from paperworks.feasibility.hai_continuous_step_v1 import (
    TASK039BR2ExecutionInterpretationV1,
)
from paperworks.v6.common import stable_hash_v1
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]


class ReportAndBoundaryTests(unittest.TestCase):
    def test_config_self_hash_and_frozen_inputs(self) -> None:
        path = ROOT / "configs/v6/task039br2_hai_continuous_step_feasibility.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        supplied = document.pop("config_hash")
        self.assertEqual(stable_hash_v1(document), supplied)
        self.assertEqual(len(document["frozen_eligibility"]["P1"]["sources"]), 12)
        self.assertEqual(len(document["frozen_eligibility"]["P3"]["targets"]), 3)

    def test_interpretation_self_hash(self) -> None:
        document = json.loads(
            (ROOT / "docs/task_reports/TASK-039BR2_EXECUTION_INTERPRETATION.json").read_text(encoding="utf-8")
        )
        TASK039BR2ExecutionInterpretationV1.from_dict(document)

    def test_all_br2_schemas_registered(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        expected = {
            "continuous_source_screening_record_v1",
            "continuous_source_event_summary_v1",
            "continuous_target_scale_record_v1",
            "continuous_directional_fit_record_v1",
            "continuous_calibration_confirmation_record_v1",
            "hai_continuous_process_feasibility_v1",
            "hai_continuous_process_selection_result_v1",
            "hai_continuous_process_freeze_v1",
            "task039br2_execution_interpretation_v1",
            "task039br2_data_access_audit_v1",
            "task039br2_execution_receipt_v1",
        }
        self.assertTrue(expected.issubset(registry.artifact_types))

    def test_rule_verifier_runtime_not_imported(self) -> None:
        tree = ast.parse((ROOT / "src/paperworks/feasibility/hai_continuous_step_v1.py").read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        )
        prohibited = ("paperworks.contracts.rule_v1", "paperworks.contracts.verifier_v1", "paperworks.contracts.runtime_v1")
        self.assertFalse(any(name.startswith(prohibited) for name in imports))

    def test_no_real_data_in_tests(self) -> None:
        for path in (
            ROOT / "tests/test_task039br2_continuous_step.py",
            ROOT / "tests/test_task039br2_contracts_and_boundaries.py",
        ):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("2022-", text)
            self.assertNotIn("attack interval", text)
            self.assertLess(path.stat().st_size, 100_000)


if __name__ == "__main__":
    unittest.main()
