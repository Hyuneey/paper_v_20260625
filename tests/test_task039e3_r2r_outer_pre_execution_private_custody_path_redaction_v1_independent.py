from __future__ import annotations

import inspect
import unittest

from scripts import remediate_task039e3_r2r_outer_pre_execution_private_custody_path_redaction_v1 as mod


def valid(**changes: object) -> mod.PrivateArtifactCandidateV1:
    values = dict(role="FROZEN_D0_PCA_MODEL_V1", expected_role="FROZEN_D0_PCA_MODEL_V1",
                  expected_hash="d" * 64, observed_hash="d" * 64)
    values.update(changes)
    return mod.PrivateArtifactCandidateV1(**values)


class OuterPreExecutionCustodyIndependentV1Tests(unittest.TestCase):
    def reject(self, call) -> None:
        with self.assertRaises(mod.OuterCustodyRemediationError):
            call()

    def test_01_forged_model_same_filename_rejected(self) -> None:
        self.reject(lambda: mod.validate_private_artifact_candidate_v1(valid(observed_hash="e" * 64)))

    def test_02_forged_model_expected_locator_rejected(self) -> None:
        self.reject(lambda: mod.validate_private_artifact_candidate_v1(valid(observed_hash="f" * 64,
                                                                            locator_differs=False)))

    def test_03_exact_hash_wrong_role_rejected(self) -> None:
        self.reject(lambda: mod.validate_private_artifact_candidate_v1(valid(role="WRONG_ROLE")))

    def test_04_threshold_substitution_rejected(self) -> None:
        self.reject(lambda: mod.validate_private_artifact_candidate_v1(valid(
            role="FROZEN_D0_THRESHOLD_AUTHORITY_V1",
            expected_role="FROZEN_D0_THRESHOLD_AUTHORITY_V1", observed_hash="0" * 64)))

    def test_05_private_root_substitution_rejected(self) -> None:
        self.reject(lambda: mod.validate_private_artifact_candidate_v1(valid(logical_binding_match=False)))

    def test_06_symlink_root_rejected(self) -> None:
        self.reject(lambda: mod.validate_custody_sentinel_candidate_v1(
            mod.CustodySentinelCandidateV1(symlink=True)))

    def test_07_nested_git_worktree_rejected(self) -> None:
        self.reject(lambda: mod.validate_custody_sentinel_candidate_v1(
            mod.CustodySentinelCandidateV1(outside_git=False)))

    def test_08_alternate_separator_encoding_detected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT\\nested\\file"
        alternate = token.replace("\\", "/")
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(alternate, (token,)))

    def test_09_drive_letter_variation_detected_by_bound_token(self) -> None:
        token = "SYNTHETIC_DRIVE:\\PRIVATE\\file"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(token, (token,)))

    def test_10_traceback_path_leak_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/traceback"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f'File "{token}", line 1', (token,)))

    def test_11_exception_chaining_leak_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/cause"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"caused by {token}", (token,)))

    def test_12_dataclass_path_serialization_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/dataclass"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"PrivateRoot(_path='{token}')", (token,)))

    def test_13_blocker_writer_locator_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/blocker"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f'{{"blocker_locator":"{token}"}}', (token,)))

    def test_14_readiness_writer_root_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/readiness"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f'{{"private_root":"{token}"}}', (token,)))

    def test_15_stdout_debug_print_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/debug"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"DEBUG {token}", (token,)))

    def test_16_stderr_logging_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/log"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"ERROR locator={token}", (token,)))

    def test_17_test_failure_path_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/test"
        self.reject(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"AssertionError: {token}", (token,)))

    def test_18_fallback_private_directory_rejected(self) -> None:
        self.reject(lambda: mod.reject_operation_v1("fallback_private_directory"))

    def test_19_copy_workaround_rejected(self) -> None:
        self.reject(lambda: mod.reject_operation_v1("private_copy"))

    def test_20_repersist_workaround_rejected(self) -> None:
        self.reject(lambda: mod.reject_operation_v1("private_repersist"))

    def test_21_test2_feature_open_rejected(self) -> None:
        self.reject(lambda: mod.validate_attempt_accounting_v1(0, 1, 0, 1, 0))

    def test_22_test2_label_open_rejected(self) -> None:
        self.reject(lambda: mod.validate_attempt_accounting_v1(0, 1, 0, 0, 1))

    def test_23_premature_attempt_increment_rejected(self) -> None:
        self.reject(lambda: mod.reject_operation_v1("scientific_attempt_increment"))

    def test_24_no_scientific_or_test2_entrypoints_in_real_path(self) -> None:
        source = inspect.getsource(mod.remediate_once_v1)
        for forbidden in ("execute_authorized_outer_v1", "hai-test2.csv", "label-test2.csv",
                          "compute_spe_float64_v1", "_evaluate_d1", "metric_values"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
