from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from paperworks.v6 import task039e3_r2r_outer_d0_d1_d2v1_execution_recovery_v1 as subject


def binding_bytes(overrides: dict[str, str] | None = None) -> bytes:
    values = {key: "PRIVATE_TOKEN" for key in subject.CANONICAL_BINDING_FIELDS}
    values.update(overrides or {})
    return ("\n".join(f"{key}='{value}'" for key, value in sorted(values.items())) + "\n").encode()


class OuterRecoveryStaticTests(unittest.TestCase):
    def rejected(self, callback) -> None:
        with self.assertRaises(subject.OuterExecutionError):
            callback()

    def test_01_exact_original_authorization_and_r2_receipt_required(self):
        observed = subject.validate_r2_infrastructure_authority_v1()
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.assertEqual(subject.R2_COMPATIBILITY_SHA256, observed["compatibility"])
        self.assertEqual(subject.AUTHORIZATION_SHA256, grant.authorization_sha256)

    def test_02_mutated_original_authorization_rejected(self):
        grant = subject.issue_committed_outer_execution_grant_v1()
        self.rejected(lambda: subject.validate_grant(replace(grant, authorization_sha256="0" * 64)))

    def test_03_exact_r2_authority_hashes_are_frozen(self):
        self.assertEqual(8, len(subject.R2_REPORTS))
        self.assertEqual("536a156a085968234db86c6650bff3c65dc3c210ce9914432c35b3f17d4872b0",
                         subject.R2_COMPATIBILITY_SHA256)

    def test_04_canonical_eight_field_binding_accepted(self):
        self.assertEqual(subject.CANONICAL_BINDING_FIELDS,
                         frozenset(subject.parse_canonical_local_bindings_v1(binding_bytes())))

    def test_05_obsolete_r1_binding_schema_rejected(self):
        raw = binding_bytes().replace(
            b"TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1=",
            b"TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1=")
        self.rejected(lambda: subject.parse_canonical_local_bindings_v1(raw))

    def test_06_missing_canonical_binding_rejected(self):
        lines = binding_bytes().splitlines()
        self.rejected(lambda: subject.parse_canonical_local_bindings_v1(b"\n".join(lines[:-1]) + b"\n"))

    def test_07_duplicate_canonical_binding_rejected(self):
        raw = binding_bytes() + binding_bytes().splitlines()[0] + b"\n"
        self.rejected(lambda: subject.parse_canonical_local_bindings_v1(raw))

    def test_08_absolute_path_comparison_is_forbidden(self):
        self.rejected(subject.reject_absolute_path_comparison_v1)

    def test_09_raw_path_token_in_stdout_rejected(self):
        self.rejected(lambda: subject.assert_path_free_surfaces_v1(("PRIVATE_TOKEN",), ("PRIVATE_TOKEN",)))

    def test_10_raw_path_token_in_stderr_rejected(self):
        self.rejected(lambda: subject.assert_path_free_surfaces_v1(("error PRIVATE_TOKEN",), ("PRIVATE_TOKEN",)))

    def test_11_raw_path_token_in_exception_rejected(self):
        self.rejected(lambda: subject.assert_path_free_surfaces_v1(("exception PRIVATE_TOKEN",), ("PRIVATE_TOKEN",)))

    def test_12_fixed_error_surface_contains_no_supplied_value(self):
        error = subject.OuterExecutionError("unsafe-private-value")
        self.assertEqual("OUTER_EXECUTION_UNEXPECTED", str(error))

    def test_13_scientific_attempt_zero_before_feature_boundary(self):
        ledger = subject.RecoveryAttemptBoundaryV1()
        self.assertEqual((0, 1, 0), (ledger.scientific_attempts, ledger.attempts_remaining, ledger.retries))

    def test_14_attempt_becomes_one_at_feature_boundary(self):
        ledger = subject.RecoveryAttemptBoundaryV1()
        ledger.begin_immediately_before_feature_access()
        self.assertEqual((1, 0, 0), (ledger.scientific_attempts, ledger.attempts_remaining, ledger.retries))

    def test_15_second_attempt_rejected(self):
        ledger = subject.RecoveryAttemptBoundaryV1()
        ledger.begin_immediately_before_feature_access()
        self.rejected(ledger.begin_immediately_before_feature_access)

    def test_16_retry_rejected(self):
        self.rejected(subject.RecoveryAttemptBoundaryV1().reject_retry)

    def test_17_label_before_all_predictions_frozen_rejected(self):
        state = subject.OuterExecutionStateMachineV1(subject.OuterExecutionState.D2_PREDICTION_FROZEN)
        self.rejected(state.require_label_access)

    def test_18_exact_original_scientific_helpers_are_delegated(self):
        source = inspect.getsource(subject.execute_authorized_outer_recovery_v1)
        self.assertIn("original.execute_authorized_outer_v1()", source)
        self.assertFalse(subject.ORIGINAL_SCIENTIFIC_EXECUTION_SEMANTICS_CHANGED)

    def test_19_d2_v1_exact_truth_table_is_unchanged(self):
        self.assertEqual((True, True, "RULE_RECOVERY"),
                         subject.fuse_point_v1(False, frozenset({"a", "b"})))
        self.assertEqual((True, False, "D0_ONLY"), subject.fuse_point_v1(True, frozenset()))

    def test_20_no_scientific_policy_knobs_exposed_by_recovery_entrypoint(self):
        signature = inspect.signature(subject.execute_authorized_outer_recovery_v1)
        self.assertEqual(0, len(signature.parameters))
        self.assertEqual(2, subject.REQUIRED_DISTINCT_SOURCES)


if __name__ == "__main__":
    unittest.main()
