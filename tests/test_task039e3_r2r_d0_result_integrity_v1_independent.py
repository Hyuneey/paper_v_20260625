from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts import audit_task039e3_r2r_d0_result_integrity_v1 as audit


class TestD0ResultIntegrityIndependentAttacksV1(unittest.TestCase):
    def test_all_declared_mutation_attacks_fail_closed(self) -> None:
        root = Path(__file__).parents[1]
        authorization = json.loads((root / audit.AUTHORIZATION_PATHS["authorization"]).read_text())
        metrics = json.loads((root / audit.METRICS_PATH).read_text())
        accounting = json.loads((root / audit.ACCOUNTING_PATH).read_text())
        attacks, accepted_invalid = audit.run_adversarial_suite_v1(
            authorization, metrics, accounting
        )
        self.assertEqual(attacks, 33)
        self.assertEqual(accepted_invalid, 0)

    def test_audit_script_does_not_import_or_call_authoritative_d0(self) -> None:
        source = (Path(__file__).parents[1] / "scripts/audit_task039e3_r2r_d0_result_integrity_v1.py").read_text()
        self.assertNotIn("import task039e3_r2r_d0_inner_execution_v1", source)
        self.assertNotIn("execute_authorized_d0_inner_v1(", source)

    def test_audit_has_no_d1_result_or_test2_path_authority(self) -> None:
        module = Path(__file__).parents[1] / "scripts/audit_task039e3_r2r_d0_result_integrity_v1.py"
        tree = __import__("ast").parse(module.read_text())
        string_literals = {
            node.value
            for node in __import__("ast").walk(tree)
            if isinstance(node, __import__("ast").Constant) and isinstance(node.value, str)
        }
        self.assertFalse(any("RULE_PREDICTION" in value for value in string_literals))
        self.assertFalse(any("hai-test2" in value.lower() for value in string_literals))
        self.assertFalse(any("label-test2" in value.lower() for value in string_literals))

    def test_report_names_are_closed_to_sanitized_audit_family(self) -> None:
        self.assertEqual(len(audit.REPORT_BASENAMES), 11)
        self.assertEqual(
            set(audit.REPORT_BASENAMES),
            {
                "FREEZE_AUDIT", "SCORE_ORACLE", "PREDICTION_AUDIT",
                "LABEL_INDEPENDENCE_AUDIT", "METRIC_ORACLE", "ACCOUNTING_AUDIT",
                "LEAKAGE_AUDIT", "INDEPENDENT_AUDIT", "READINESS", "BUNDLE", "RECEIPT",
            },
        )


if __name__ == "__main__":
    unittest.main()
