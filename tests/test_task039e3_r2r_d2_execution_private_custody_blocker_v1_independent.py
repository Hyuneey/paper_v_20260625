from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_task039e3_r2r_d2_execution_private_custody_blocker_v1.py"
SPEC = importlib.util.spec_from_file_location("d2_blocker_audit_independent", SCRIPT)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def valid_snapshot() -> dict[str, object]:
    public = audit.audit_public_repository_v1(ROOT)
    private = {
        "final_private_fusion_evidence_exists": False,
        "partial_private_temp_exists": False,
        "zero_byte_private_target_exists": False,
        "stale_private_residue_count": 0,
        "private_evidence_directory_residue": True,
        "tracked_private_path_occurrences": 0,
        "tracked_private_path_leak": False,
        "path_present_in_exception_object": True,
        "path_present_in_stderr": True,
        "path_present_in_stdout": False,
        "path_present_in_user_facing_channel": True,
        "path_present_in_tracked_blocker_json": False,
        "path_present_in_tracked_blocker_markdown": False,
        "path_present_in_tracked_source_test_artifact": False,
        "path_present_in_project_state": False,
        "path_present_in_git_commit_diff": False,
        "path_present_in_other_tracked_output": False,
        "path_exposure_classification": audit.PATH_EXPOSURE_CLASSIFICATION,
        "scientific_artifact_compromised": False,
    }
    return audit.build_recovery_snapshot_v1(public, private)


class TestIndependentD2PrivateCustodyBlockerAuditV1(unittest.TestCase):
    def test_mutation_attack_matrix(self) -> None:
        base = valid_snapshot()
        mutations = (
            ("blocker_hash", "f" * 64),
            ("execution_implementation_commit_a", "e" * 40),
            ("d2_design_hash", "0" * 64),
            ("authorization_hash", "1" * 64),
            ("d0_prediction_hash", "2" * 64),
            ("d1_prediction_hash", "3" * 64),
            ("source_map_hash", "4" * 64),
            ("execution_last_completed_state", "FUSION_COMPUTED"),
            ("combined_prediction_frozen", True),
            ("combined_prediction_exists", True),
            ("label_scientific_parses", 1),
            ("label_before_combined_prediction_access", True),
            ("metric_computations", 1),
            ("d2_result_observed", True),
            ("scientific_inputs_changed", True),
            ("policy_changed", True),
            ("test2_accesses", 1),
            ("tracked_private_path_occurrences", 1),
            ("tracked_private_path_leak", True),
            ("partial_private_temp_exists", True),
            ("root_cause_classification", "PRIVATE_WRITER_IMPLEMENTATION_DEFECT"),
            ("future_total_execution_attempts", 1),
            ("future_result_driven_retries", 1),
            ("recovery_eligible", False),
        )
        accepted = 0
        for key, value in mutations:
            candidate = copy.deepcopy(base)
            candidate[key] = value
            try:
                audit.validate_recovery_snapshot_v1(candidate)
            except audit.BlockerAuditV1Error:
                continue
            accepted += 1
        self.assertEqual(len(mutations), audit.INDEPENDENT_ATTACKS)
        self.assertEqual(accepted, 0)

    def test_wrong_blocker_hash_rejected_even_when_self_rehashed(self) -> None:
        blocker = audit._strict_object((ROOT / audit.BLOCKER_JSON).read_bytes())
        blocker["blocker_code"] = "WRONG"
        blocker = audit.self_hash_document_v1(blocker)
        self.assertNotEqual(blocker["artifact_hash"], audit.BLOCKER_HASH)

    def test_unexpected_combined_prediction_guard_is_exact(self) -> None:
        snapshot = valid_snapshot()
        snapshot["combined_prediction_exists"] = True
        with self.assertRaises(audit.BlockerAuditV1Error):
            audit.validate_recovery_snapshot_v1(snapshot)

    def test_permission_and_path_policy_are_not_scientific(self) -> None:
        snapshot = valid_snapshot()
        self.assertEqual(snapshot["root_cause_classification"], "PRIVATE_PARENT_PERMISSION_DENIED")
        self.assertFalse(snapshot["root_cause_scientific"])
        self.assertFalse(snapshot["root_cause_result_driven"])


if __name__ == "__main__":
    unittest.main()
