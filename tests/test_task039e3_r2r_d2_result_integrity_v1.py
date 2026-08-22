from __future__ import annotations

import ast
import copy
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d2_result_integrity_audit_v1",
    ROOT / "scripts" / "audit_task039e3_r2r_d2_result_integrity_v1.py",
)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class D2ResultIntegrityAuditV1Tests(unittest.TestCase):
    def test_frozen_authority_constants(self) -> None:
        self.assertEqual(AUDIT.EXPECTED_ROWS, 54_000)
        self.assertEqual(AUDIT.REQUIRED_DISTINCT_SOURCE_COUNT, 2)
        self.assertEqual(AUDIT.D2_DESIGN_HASH, "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51")
        self.assertEqual(AUDIT.COMBINED_PREDICTION_HASH, "cf1005a03d98481b57c3ce2ad74db3e2e5d2dc3a1983d60e0aedb4f46c83b3f5")

    def test_independent_truth_table(self) -> None:
        result = AUDIT.fuse_rows_independently_v1(
            (False, True, False, True),
            ((0, False, "a"), (1, False, "a"), (2, True, "a"),
             (2, True, "b"), (3, True, "a"), (3, True, "b")),
            {"a": "S1", "b": "S2"},
        )
        self.assertEqual(
            result["triggers"],
            ("NONE", "D0_ONLY", "RULE_RECOVERY", "D0_AND_RULE_CORROBORATION"),
        )
        self.assertEqual(result["alarms"], (False, True, True, True))
        self.assertEqual(result["d0_preservation_violations"], 0)

    def test_same_source_duplicates_collapse(self) -> None:
        result = AUDIT.fuse_rows_independently_v1(
            (False,), ((0, True, "a"), (0, True, "b")),
            {"a": "SAME", "b": "SAME"},
        )
        self.assertEqual(result["sources"], (("SAME",),))
        self.assertEqual(result["triggers"], ("NONE",))

    def test_same_second_exactness(self) -> None:
        result = AUDIT.fuse_rows_independently_v1(
            (False, False), ((0, True, "a"), (1, True, "b")),
            {"a": "S1", "b": "S2"},
        )
        self.assertEqual(result["corroboration"], (False, False))

    def test_unknown_binding_rejected(self) -> None:
        with self.assertRaises(AUDIT.D2ResultIntegrityAuditError):
            AUDIT.fuse_rows_independently_v1((False,), ((0, True, "x"),), {})

    def test_contiguous_episode_oracle(self) -> None:
        self.assertEqual(AUDIT.contiguous_runs_v1((1, 2, 4, 8, 9)), ((1, 3), (4, 5), (8, 10)))
        with self.assertRaises(AUDIT.D2ResultIntegrityAuditError):
            AUDIT.contiguous_runs_v1((1, 1))

    def test_attack_event_oracle(self) -> None:
        self.assertEqual(AUDIT.attack_events_v1((0, 1, 1, 0, 1)), ((1, 3), (4, 5)))
        with self.assertRaises(AUDIT.D2ResultIntegrityAuditError):
            AUDIT.attack_events_v1((0, 2))

    def test_metric_counts(self) -> None:
        attacks = ((2, 4), (8, 10))
        episodes = ((0, 1), (3, 5), (12, 14))
        self.assertEqual(AUDIT.metric_counts_v1(attacks, episodes), (1, 2))

    def test_decision_identity_binds_alarm_and_trigger(self) -> None:
        base = AUDIT.combined_decision_identity_v1(7, True, "D0_ONLY")
        self.assertNotEqual(base, AUDIT.combined_decision_identity_v1(7, False, "NONE"))
        self.assertNotEqual(base, AUDIT.combined_decision_identity_v1(8, True, "D0_ONLY"))

    def test_prediction_closure_and_identity(self) -> None:
        alarms = (False, True)
        triggers = ("NONE", "D0_ONLY")
        records = [
            {
                "physical_row_index": index,
                "d2_alarm_emitted": alarm,
                "trigger_class": trigger,
                "combined_decision_identity": AUDIT.combined_decision_identity_v1(index, alarm, trigger),
            }
            for index, (alarm, trigger) in enumerate(zip(alarms, triggers))
        ]
        AUDIT.validate_prediction_rows_v1(records, alarms, triggers)
        records[1]["d2_alarm_emitted"] = False
        with self.assertRaises(AUDIT.D2ResultIntegrityAuditError):
            AUDIT.validate_prediction_rows_v1(records, alarms, triggers)

    def test_contract_exact_and_mutation_rejected(self) -> None:
        contract = AUDIT.expected_audit_contract_v1()
        AUDIT.validate_audit_contract_v1(contract)
        for key, value in (
            ("total_attempts", 1),
            ("third_attempt_authorized", True),
            ("test2_accesses", 1),
            ("result_driven_retry", True),
        ):
            mutated = {**contract, key: value}
            with self.assertRaises(AUDIT.D2ResultIntegrityAuditError):
                AUDIT.validate_audit_contract_v1(mutated)

    def test_adversarial_suite_rejects_every_case(self) -> None:
        attacks, accepted = AUDIT.run_adversarial_suite_v1()
        self.assertEqual(attacks, 50)
        self.assertEqual(accepted, 0)

    def test_self_hash_rejects_self_rehash_mutation(self) -> None:
        doc = AUDIT.self_hashed_v1({"artifact_type": "Synthetic", "value": 1})
        AUDIT.validate_self_hash_v1(doc)
        forged = copy.deepcopy(doc)
        forged["value"] = 2
        with self.assertRaises(AUDIT.D2ResultIntegrityAuditError):
            AUDIT.validate_self_hash_v1(forged)

    def test_public_result_commit_files_are_byte_frozen(self) -> None:
        outcome = AUDIT.audit_git_freeze_v1(ROOT)
        self.assertEqual(outcome["post_result_freeze_mutations"], 0)
        self.assertEqual(outcome["production_changes_after_commit_a"], 0)

    def test_audit_source_does_not_import_production_science(self) -> None:
        source = (ROOT / "scripts" / "audit_task039e3_r2r_d2_result_integrity_v1.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {
            "fuse_point_v1", "fuse_synthetic_timeline_v1", "_build_fusion_evidence_v1",
            "_build_combined_prediction_v1", "compute_metric_values_v1", "metric_counts_v1",
            "form_alarm_episodes_v1", "derive_attack_events_v1", "execute_authorized_d2_inner_v1",
        }
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
        called = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertFalse(any("task039e3_r2r_d2_inner_execution" in name for name in imported))
        self.assertFalse(called & (forbidden - {"metric_counts_v1"}))


if __name__ == "__main__":
    unittest.main()
