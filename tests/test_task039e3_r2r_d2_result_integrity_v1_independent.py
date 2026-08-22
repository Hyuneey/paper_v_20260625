from __future__ import annotations

import ast
import copy
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d2_result_integrity_audit_v1_independent",
    ROOT / "scripts" / "audit_task039e3_r2r_d2_result_integrity_v1.py",
)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class D2ResultIntegrityIndependentV1Tests(unittest.TestCase):
    def test_six_semantic_differential_cases(self) -> None:
        cases = (
            ((False,), (), {"a": "S1"}, ("NONE",)),
            ((True,), (), {"a": "S1"}, ("D0_ONLY",)),
            ((False,), ((0, True, "a"), (0, True, "b")), {"a": "S1", "b": "S2"}, ("RULE_RECOVERY",)),
            ((True,), ((0, True, "a"), (0, True, "b")), {"a": "S1", "b": "S2"}, ("D0_AND_RULE_CORROBORATION",)),
            ((False,), ((0, True, "a"), (0, True, "b")), {"a": "S1", "b": "S1"}, ("NONE",)),
            ((False, False), ((0, True, "a"), (1, True, "b")), {"a": "S1", "b": "S2"}, ("NONE", "NONE")),
        )
        for d0, d1, source_map, triggers in cases:
            with self.subTest(triggers=triggers):
                self.assertEqual(AUDIT.fuse_rows_independently_v1(d0, d1, source_map)["triggers"], triggers)

    def test_source_count_change_changes_semantics_and_is_not_authority(self) -> None:
        d1 = ((0, True, "a"), (0, True, "b"))
        mapping = {"a": "S1", "b": "S2"}
        self.assertEqual(AUDIT.fuse_rows_independently_v1((False,), d1, mapping)["triggers"], ("RULE_RECOVERY",))
        self.assertEqual(AUDIT.fuse_rows_independently_v1((False,), d1, mapping, required_distinct_sources=3)["triggers"], ("NONE",))

    def test_alarm_mutation_rejected_even_when_identity_is_rehashed(self) -> None:
        alarms = (False, True)
        triggers = ("NONE", "D0_ONLY")
        records = [
            {"physical_row_index": i, "d2_alarm_emitted": a, "trigger_class": t,
             "combined_decision_identity": AUDIT.combined_decision_identity_v1(i, a, t)}
            for i, (a, t) in enumerate(zip(alarms, triggers))
        ]
        mutated = copy.deepcopy(records)
        mutated[1]["d2_alarm_emitted"] = False
        mutated[1]["trigger_class"] = "NONE"
        mutated[1]["combined_decision_identity"] = AUDIT.combined_decision_identity_v1(1, False, "NONE")
        with self.assertRaises(AUDIT.D2ResultIntegrityAuditError):
            AUDIT.validate_prediction_rows_v1(mutated, alarms, triggers)

    def test_label_injection_rejected(self) -> None:
        record = {"physical_row_index": 0, "d2_alarm_emitted": False, "trigger_class": "NONE",
                  "combined_decision_identity": AUDIT.combined_decision_identity_v1(0, False, "NONE"),
                  "label": 0}
        with self.assertRaises(AUDIT.D2ResultIntegrityAuditError):
            AUDIT.validate_prediction_rows_v1((record,), (False,), ("NONE",))

    def test_metric_formulas_are_frozen(self) -> None:
        self.assertEqual(set(AUDIT.METRIC_FORMULAS), set(AUDIT.EXPECTED_METRIC_VALUES))
        self.assertEqual(AUDIT.METRIC_FORMULAS["incremental_normal_far_episodes_per_hour"], AUDIT.INCREMENTAL_FAR_FORMULA)
        self.assertNotEqual(AUDIT.EXPECTED_ADDED_FAR, AUDIT.EXPECTED_INCREMENTAL_FAR)

    def test_no_authoritative_controller_or_helper_reference(self) -> None:
        source = (ROOT / "scripts" / "audit_task039e3_r2r_d2_result_integrity_v1.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        forbidden = {
            "execute_authorized_d2_inner_v1", "execute_authorized_d2_inner_recovery_v1",
            "_build_fusion_evidence_v1", "_build_combined_prediction_v1",
            "fuse_point_v1", "fuse_synthetic_timeline_v1",
        }
        self.assertFalse((names | attrs) & forbidden)

    def test_report_inventory_is_exact(self) -> None:
        self.assertEqual(len(AUDIT.REPORT_NAMES), 13)
        self.assertEqual(AUDIT.REPORT_NAMES[-3:], ("READINESS", "BUNDLE", "RECEIPT"))
        self.assertEqual(len(AUDIT.RESULT_C_PATHS), 8)

    def test_every_adversarial_case_rejected(self) -> None:
        self.assertEqual(AUDIT.run_adversarial_suite_v1(), (50, 0))


if __name__ == "__main__":
    unittest.main()
