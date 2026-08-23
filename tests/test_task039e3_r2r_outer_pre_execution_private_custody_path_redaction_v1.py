from __future__ import annotations

import inspect
import unittest

from scripts import remediate_task039e3_r2r_outer_pre_execution_private_custody_path_redaction_v1 as mod


def candidate(**changes: object) -> mod.PrivateArtifactCandidateV1:
    base = dict(
        role="FROZEN_D0_PCA_MODEL_V1",
        expected_role="FROZEN_D0_PCA_MODEL_V1",
        expected_hash="a" * 64,
        observed_hash="a" * 64,
    )
    base.update(changes)
    return mod.PrivateArtifactCandidateV1(**base)


class OuterPreExecutionCustodyRemediationV1Tests(unittest.TestCase):
    def assertRejected(self, call) -> None:
        with self.assertRaises(mod.OuterCustodyRemediationError):
            call()

    def test_01_correct_model_binding_accepted(self) -> None:
        self.assertEqual(mod.validate_private_artifact_candidate_v1(candidate()), "a" * 64)

    def test_02_wrong_model_hash_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_private_artifact_candidate_v1(
            candidate(observed_hash="b" * 64)))

    def test_03_wrong_model_role_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_private_artifact_candidate_v1(
            candidate(role="FORGED_ROLE")))

    def test_04_correct_threshold_binding_accepted(self) -> None:
        value = candidate(role="FROZEN_D0_THRESHOLD_AUTHORITY_V1",
                          expected_role="FROZEN_D0_THRESHOLD_AUTHORITY_V1")
        self.assertEqual(mod.validate_private_artifact_candidate_v1(value), "a" * 64)

    def test_05_threshold_hash_mutation_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_private_artifact_candidate_v1(
            candidate(role="FROZEN_D0_THRESHOLD_AUTHORITY_V1",
                      expected_role="FROZEN_D0_THRESHOLD_AUTHORITY_V1",
                      observed_hash="c" * 64)))

    def test_06_environment_local_difference_accepted(self) -> None:
        value = candidate(locator_differs=True, absolute_path_equality_required=False)
        self.assertEqual(mod.validate_private_artifact_candidate_v1(value), "a" * 64)

    def test_07_absolute_path_as_authority_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_private_artifact_candidate_v1(
            candidate(absolute_path_equality_required=True)))

    def test_08_inside_git_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_private_artifact_candidate_v1(
            candidate(outside_git=False)))

    def test_09_symlink_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_private_artifact_candidate_v1(
            candidate(symlink=True)))

    def test_10_tracked_duplicate_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_private_artifact_candidate_v1(
            candidate(tracked_copy_count=1)))

    def test_11_unwritable_custody_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_custody_sentinel_candidate_v1(
            mod.CustodySentinelCandidateV1(writable=False)))

    def test_12_sentinel_residue_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_custody_sentinel_candidate_v1(
            mod.CustodySentinelCandidateV1(residue_count=1)))

    def test_13_raw_path_in_exception_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/secret"
        self.assertRejected(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"Exception: {token}", (token,)))

    def test_14_raw_path_in_stdout_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/stdout"
        self.assertRejected(lambda: mod.OuterPrivatePathRedactionV1.require_clean(token, (token,)))

    def test_15_raw_path_in_stderr_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/stderr"
        self.assertRejected(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"stderr={token}", (token,)))

    def test_16_raw_path_in_json_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/json"
        self.assertRejected(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f'{{"locator":"{token}"}}', (token,)))

    def test_17_raw_path_in_markdown_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/markdown"
        self.assertRejected(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"`{token}`", (token,)))

    def test_18_pathlib_repr_rejected(self) -> None:
        token = "SYNTHETIC_PRIVATE_ROOT/repr"
        self.assertRejected(lambda: mod.OuterPrivatePathRedactionV1.require_clean(
            f"PosixPath('{token}')", (token,)))

    def test_19_escaped_path_rejected(self) -> None:
        token = "SYNTHETIC_DRIVE:\\PRIVATE\\artifact"
        payload = token.replace("\\", "\\\\")
        self.assertRejected(lambda: mod.OuterPrivatePathRedactionV1.require_clean(payload, (token,)))

    def test_20_fixed_symbolic_error_accepted(self) -> None:
        code = "OUTER_PRIVATE_CUSTODY_MODEL_HASH_MISMATCH"
        self.assertEqual(mod.OuterPrivatePathRedactionV1.error_code(
            mod.OuterCustodyRemediationError(code)), code)

    def test_21_attempt_counter_remains_zero(self) -> None:
        self.assertEqual(mod.validate_attempt_accounting_v1(0, 1, 0, 0, 0),
                         "OUTER_ONE_SHOT_AUTHORIZATION_STILL_AVAILABLE")

    def test_22_attempt_increment_rejected(self) -> None:
        self.assertRejected(lambda: mod.validate_attempt_accounting_v1(1, 0, 0, 0, 0))

    def test_23_test2_feature_access_rejected(self) -> None:
        self.assertRejected(lambda: mod.reject_operation_v1("test2_feature_access"))

    def test_24_test2_label_access_rejected(self) -> None:
        self.assertRejected(lambda: mod.reject_operation_v1("test2_label_access"))

    def test_25_exact_namespaces_accepted(self) -> None:
        self.assertEqual(mod.validate_namespace_set_v1(mod.NAMESPACES),
                         "OUTER_PRIVATE_CUSTODY_NAMESPACES_READY")

    def test_26_namespace_substitution_rejected(self) -> None:
        changed = list(mod.NAMESPACES)
        changed[0] = "SUBSTITUTED_NAMESPACE"
        self.assertRejected(lambda: mod.validate_namespace_set_v1(changed))

    def test_27_private_copy_rejected(self) -> None:
        self.assertRejected(lambda: mod.reject_operation_v1("private_copy"))

    def test_28_private_move_rejected(self) -> None:
        self.assertRejected(lambda: mod.reject_operation_v1("private_move"))

    def test_29_private_rewrite_rejected(self) -> None:
        self.assertRejected(lambda: mod.reject_operation_v1("private_rewrite"))

    def test_30_self_hash_field_collision_rejected(self) -> None:
        self.assertRejected(lambda: mod.seal({"artifact_hash": "x"}))

    def test_31_duplicate_json_key_rejected(self) -> None:
        self.assertRejected(lambda: mod.strict_json(b'{"x":1,"x":2}'))

    def test_32_real_outer_entrypoint_not_imported(self) -> None:
        source = inspect.getsource(mod)
        self.assertNotIn("task039e3_r2r_outer_d0_d1_d2v1_execution_v1 as", source)
        self.assertNotIn("execute_authorized_outer_v1", source)


if __name__ == "__main__":
    unittest.main()
