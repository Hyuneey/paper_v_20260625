from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_task039e3_r2r_d2_execution_private_custody_blocker_v1.py"
SPEC = importlib.util.spec_from_file_location("d2_blocker_audit", SCRIPT)
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


class TestD2PrivateCustodyBlockerAuditV1(unittest.TestCase):
    def test_exact_public_blocker_replay(self) -> None:
        result = audit.audit_public_repository_v1(ROOT)
        self.assertTrue(result["blocker_hash_match"])
        self.assertEqual(result["execution_last_completed_state"], "SOURCE_MAP_VALIDATED")
        self.assertEqual(
            result["fusion_computation_classification"],
            "FUSION_COMPUTED_IN_MEMORY_BUT_NOT_PERSISTED",
        )

    def test_opaque_prediction_and_source_identity_replay(self) -> None:
        result = audit.audit_public_repository_v1(ROOT)
        for key in (
            "d2_design_hash_match", "d2_authorization_hash_match",
            "d0_prediction_hash_match", "d1_prediction_hash_match", "source_map_hash_match",
        ):
            self.assertTrue(result[key])

    def test_execution_source_and_writer_are_frozen(self) -> None:
        result = audit.audit_public_repository_v1(ROOT)
        self.assertEqual(result["execution_source_sha256"], audit.EXECUTION_SOURCE_SHA256)
        self.assertEqual(
            result["private_fusion_evidence_writer_classification"],
            audit.WRITER_CLASSIFICATION,
        )

    def test_combined_prediction_absent(self) -> None:
        self.assertFalse((ROOT / audit.COMBINED_PREDICTION).exists())

    def test_recovery_snapshot_exact(self) -> None:
        snapshot = valid_snapshot()
        self.assertTrue(snapshot["recovery_eligible"])
        self.assertEqual(snapshot["future_total_execution_attempts"], 2)

    def test_ephemeral_and_tracked_path_classification(self) -> None:
        self.assertEqual(
            audit.classify_path_exposure_v1(tracked_occurrences=0, ephemeral_exposure=True),
            "EPHEMERAL_PRIVATE_PATH_DISCLOSURE",
        )
        self.assertEqual(
            audit.classify_path_exposure_v1(tracked_occurrences=1, ephemeral_exposure=True),
            "TRACKED_PRIVATE_PATH_LEAK_REQUIRES_SANITIZATION",
        )

    def test_residue_classification(self) -> None:
        residue = audit.classify_residue_v1(
            final_exists=False, temp_exists=True, final_size=None, targeted_entries=1
        )
        self.assertTrue(residue["partial_private_temp_exists"])
        self.assertEqual(residue["stale_private_residue_count"], 1)

    def test_missing_private_binding_rejected_without_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(audit.BlockerAuditV1Error) as context:
                audit._binding_values(Path(temporary) / "missing")
        self.assertEqual(context.exception.code, "PRIVATE_BINDING_MISSING")

    def test_invalid_recovery_cannot_be_called_attempt_one(self) -> None:
        snapshot = valid_snapshot()
        snapshot["future_total_execution_attempts"] = 1
        with self.assertRaises(audit.BlockerAuditV1Error):
            audit.validate_recovery_snapshot_v1(snapshot)

    def test_result_driven_retry_rejected(self) -> None:
        snapshot = valid_snapshot()
        snapshot["future_result_driven_retries"] = 1
        with self.assertRaises(audit.BlockerAuditV1Error):
            audit.validate_recovery_snapshot_v1(snapshot)


if __name__ == "__main__":
    unittest.main()
