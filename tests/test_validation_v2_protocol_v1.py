from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.prediction_custody_v1 import (
    D1PredictionArtifactV2,
    D1PredictionRecordV2,
    PredictionCustodyError,
    authorize_label_access_v1,
    persist_prediction_before_label_v1,
)
from paperworks.validation_v2.protocol_v1 import (
    EventMetricPolicyV1,
    ProtocolExecutionGuardV1,
    ProtocolGuardStateV1,
    ProtocolOperationV1,
    ValidationProtocolError,
    build_policy_freeze_receipt_v1,
    build_validation_protocol_v1,
    validate_policy_freeze_receipt_v1,
    validate_validation_protocol_v1,
)


COMMIT = "a" * 40


class ValidationProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.custody_root = Path(self.temporary.name).resolve()
        self.protocol = build_validation_protocol_v1(source_commit=COMMIT)
        self.receipt = build_policy_freeze_receipt_v1(
            protocol=self.protocol,
            candidate_set_hash="b" * 64,
            selection_objective="NORMAL_ONLY_PREREGISTERED_OBJECTIVE",
            tie_break_rule="LEXICOGRAPHIC_CONFIG_ID",
            selected_config_hash="c" * 64,
            authority_hash="d" * 64,
            method_policy_hashes=("e" * 64, "f" * 64),
            metric_contract_hash="1" * 64,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def label_capability(self, *, authority_hash: str = "d" * 64):
        prediction_path = "custody/prediction.json"
        receipt_path = "custody/receipt.json"
        artifact = D1PredictionArtifactV2(
            method_id="VALIDATION-V2-D1", config_id="V2-CONFIG-001",
            experiment_id="EXP-04-DEVELOPMENT", dataset_id="HAI-P1-DEVELOPMENT",
            split_role="DEVELOPMENT_TEST1", authority_hash=authority_hash,
            runtime_authorization_hash="2" * 64, execution_context_hash="3" * 64,
            source_commit=COMMIT, portfolio_hash="4" * 64, file_contract_hash="5" * 64,
            records=(D1PredictionRecordV2("file-a", "6" * 64, 0, False),),
        )
        persist_prediction_before_label_v1(
            artifact, artifact_root=self.custody_root,
            prediction_relative_path=prediction_path, receipt_relative_path=receipt_path,
        )
        capability = authorize_label_access_v1(
            artifact_root=self.custody_root, prediction_relative_path=prediction_path,
            receipt_relative_path=receipt_path, expected_authority_hash=authority_hash,
            expected_runtime_authorization_hash="2" * 64, expected_execution_context_hash="3" * 64,
            expected_source_commit=COMMIT, expected_portfolio_hash="4" * 64,
            expected_file_contract_hash="5" * 64,
        )
        return capability, self.custody_root / receipt_path

    def test_exact_roles_are_frozen_without_heldout_authority(self) -> None:
        roles = {item.split_id: item.role.value for item in self.protocol.split_assignments}
        self.assertEqual(roles, {
            "train1": "NORMAL_FIT_PRIMARY", "train2": "NORMAL_FIT_SECONDARY",
            "train3": "NORMAL_CONFIRMATION_CALIBRATION", "train4": "NORMAL_POLICY_SELECTION_SANITY",
            "test1": "DEVELOPMENT_ONLY", "future_heldout": "FUTURE_FINAL_HELDOUT",
        })
        self.assertFalse(self.protocol.heldout_authorized)
        self.assertEqual(self.protocol.selection_split, "train4")
        self.assertEqual(self.protocol.development_split, "test1")

    def test_event_and_far_contract_is_pa_free_file_local_and_conservative(self) -> None:
        policy = self.protocol.event_metric_policy
        self.assertEqual(policy.sampling_seconds, 1)
        self.assertEqual(policy.event_construction, "MAXIMAL_CONTIGUOUS_POSITIVE_RUN_HALF_OPEN")
        self.assertEqual(policy.event_hit_rule, "ANY_ALARM_SECOND_INSIDE_SAME_FILE_HALF_OPEN_EVENT")
        self.assertEqual(policy.point_adjustment, "PROHIBITED")
        self.assertEqual(policy.episode_allowed_gap_seconds, 0)
        self.assertEqual(policy.mixed_episode_policy, "ANY_ATTACK_OVERLAP_EXCLUDES_WHOLE_EPISODE_FROM_NORMAL_FP")
        self.assertEqual(policy.zero_normal_exposure, "UNDEFINED")
        self.assertEqual(policy.zero_attack_events, "UNDEFINED")
        self.assertEqual(policy.event_independence, "NOT_ESTABLISHED")
        self.assertEqual(policy.d1_common_alarm_states, ("FAIL",))
        self.assertIn("NO_OPPORTUNITY", policy.d1_common_no_alarm_states)

    def test_mutated_event_policy_rejected(self) -> None:
        for kwargs in ({"sampling_seconds": 2}, {"grace_window_seconds": 1}, {"episode_allowed_gap_seconds": 1}, {"point_adjustment": "ENABLED"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValidationProtocolError):
                EventMetricPolicyV1(**kwargs)

    def test_protocol_hash_is_deterministic_and_replayed(self) -> None:
        second = build_validation_protocol_v1(source_commit=COMMIT)
        self.assertEqual(self.protocol.protocol_hash, second.protocol_hash)
        self.assertEqual(validate_validation_protocol_v1(self.protocol), self.protocol.protocol_hash)
        with self.assertRaisesRegex(ValidationProtocolError, "PROTOCOL_REPLAY_MISMATCH"):
            validate_validation_protocol_v1(replace(self.protocol, no_post_test_tuning=False))

    def test_policy_freeze_receipt_is_bound_and_self_hashed(self) -> None:
        self.assertEqual(validate_policy_freeze_receipt_v1(self.receipt, protocol=self.protocol), self.receipt.receipt_hash)
        with self.assertRaisesRegex(ValidationProtocolError, "REPLAY_MISMATCH"):
            validate_policy_freeze_receipt_v1(replace(self.receipt, tie_break_rule="CHANGED"), protocol=self.protocol)

    def test_policy_freeze_receipt_rejects_missing_provenance(self) -> None:
        with self.assertRaisesRegex(ValidationProtocolError, "MISSING_METHOD_POLICY_HASHES"):
            build_policy_freeze_receipt_v1(
                protocol=self.protocol, candidate_set_hash="b" * 64,
                selection_objective="objective", tie_break_rule="rule",
                selected_config_hash="c" * 64, authority_hash="d" * 64,
                method_policy_hashes=(), metric_contract_hash="1" * 64,
            )

    def test_invalid_source_commit_rejected(self) -> None:
        for value in ("", "z" * 40, "a" * 39, "a" * 41):
            with self.subTest(value=value), self.assertRaisesRegex(ValidationProtocolError, "INVALID_SOURCE_COMMIT"):
                build_validation_protocol_v1(source_commit=value)

    def test_normal_operations_are_split_restricted(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        guard.authorize(split_id="train1", operation=ProtocolOperationV1.CANDIDATE_LEARNING)
        guard.authorize(split_id="train3", operation=ProtocolOperationV1.RELATION_CONFIRMATION)
        guard.authorize(split_id="train4", operation=ProtocolOperationV1.NORMAL_POLICY_SELECTION)
        with self.assertRaisesRegex(ValidationProtocolError, "OPERATION_NOT_ALLOWED_FOR_SPLIT"):
            guard.authorize(split_id="train3", operation=ProtocolOperationV1.NORMAL_POLICY_SELECTION)

    def test_development_prediction_requires_policy_freeze(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        with self.assertRaisesRegex(ValidationProtocolError, "BEFORE_POLICY_FREEZE"):
            guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION)
        guard.freeze_policies(self.receipt)
        guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION)

    def test_label_access_requires_durable_prediction_freeze(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        guard.freeze_policies(self.receipt)
        with self.assertRaisesRegex(ValidationProtocolError, "LABEL_ACCESS_BEFORE_DURABLE"):
            guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS)
        guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION)
        guard.record_development_prediction_frozen()
        with self.assertRaisesRegex(ValidationProtocolError, "LABEL_ACCESS_BEFORE_DURABLE"):
            guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS)
        capability, _ = self.label_capability()
        guard.authorize(
            split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS,
            label_access_capability=capability,
        )

    def test_full_guard_sequence(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        guard.freeze_policies(self.receipt)
        guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION)
        guard.record_development_prediction_frozen()
        capability, _ = self.label_capability()
        guard.authorize(
            split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS,
            label_access_capability=capability,
        )
        guard.record_development_labels_accessed()
        guard.complete()
        self.assertIs(guard.state, ProtocolGuardStateV1.COMPLETE)

    def test_selection_after_policy_freeze_is_rejected(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        guard.freeze_policies(self.receipt)
        with self.assertRaisesRegex(ValidationProtocolError, "SELECTION_OR_FIT_AFTER_POLICY_FREEZE"):
            guard.authorize(split_id="train4", operation=ProtocolOperationV1.NORMAL_POLICY_SELECTION)

    def test_post_test_tuning_is_rejected(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        guard.freeze_policies(self.receipt)
        guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION)
        guard.record_development_prediction_frozen()
        capability, _ = self.label_capability()
        guard.authorize(
            split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS,
            label_access_capability=capability,
        )
        guard.record_development_labels_accessed()
        with self.assertRaisesRegex(ValidationProtocolError, "POST_TEST_TUNING"):
            guard.authorize(split_id="train4", operation=ProtocolOperationV1.NORMAL_POLICY_SELECTION)

    def test_heldout_aliases_and_future_split_are_not_authorized(self) -> None:
        for split in ("test2", "outer", "heldout", "sealed"):
            with self.subTest(split=split), self.assertRaisesRegex(ValidationProtocolError, "UNAUTHORIZED_HELDOUT_ALIAS"):
                ProtocolExecutionGuardV1(self.protocol).authorize(split_id=split, operation=ProtocolOperationV1.FINAL_PREDICTION)
        with self.assertRaisesRegex(ValidationProtocolError, "OPERATION_NOT_ALLOWED_FOR_SPLIT"):
            ProtocolExecutionGuardV1(self.protocol).authorize(split_id="future_heldout", operation=ProtocolOperationV1.FINAL_PREDICTION)

    def test_reporting_contract_separates_development_and_validation(self) -> None:
        reporting = self.protocol.reporting_policy
        self.assertEqual(reporting.evaluation_status, "DEVELOPMENT_ONLY")
        self.assertIn("scientific_validation_status", reporting.required_status_fields)
        self.assertIn("heldout_status", reporting.required_status_fields)
        self.assertEqual(reporting.inferential_statistics, "NONE_UNLESS_SEPARATELY_PREREGISTERED")
        self.assertTrue(self.protocol.hyperparameter_provenance_required)
        self.assertTrue(self.protocol.policy_freeze_receipt_required)
        self.assertIn("defined", reporting.required_metric_fields)
        self.assertIn("failure_code", reporting.required_failure_fields)

    def test_state_transitions_require_prior_authorization(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        guard.freeze_policies(self.receipt)
        with self.assertRaisesRegex(ValidationProtocolError, "WITHOUT_AUTHORIZATION"):
            guard.record_development_prediction_frozen()

    def test_authorize_rejects_raw_string_enum_and_non_string_split(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        with self.assertRaisesRegex(ValidationProtocolError, "SPLIT_ID_MUST_BE_EXACT_STRING"):
            guard.authorize(split_id=1, operation=ProtocolOperationV1.CANDIDATE_LEARNING)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValidationProtocolError, "OPERATION_MUST_BE_EXACT_PROTOCOL_ENUM"):
            guard.authorize(split_id="train1", operation="CANDIDATE_LEARNING")  # type: ignore[arg-type]
        guard.freeze_policies(self.receipt)
        with self.assertRaisesRegex(ValidationProtocolError, "OPERATION_MUST_BE_EXACT_PROTOCOL_ENUM"):
            guard.authorize(split_id="test1", operation="DEVELOPMENT_PREDICTION")  # type: ignore[arg-type]

    def test_label_authorization_rejects_bare_boolean_wrong_authority_and_stale_receipt(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        guard.freeze_policies(self.receipt)
        guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION)
        guard.record_development_prediction_frozen()
        with self.assertRaisesRegex(ValidationProtocolError, "LABEL_CAPABILITY_MUST_BE_EXACT_CUSTODY_TYPE"):
            guard.authorize(
                split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS,
                label_access_capability=True,  # type: ignore[arg-type]
            )

        wrong_capability, _ = self.label_capability(authority_hash="e" * 64)
        with self.assertRaisesRegex(PredictionCustodyError, "LABEL_CAPABILITY_AUTHORITY_MISMATCH"):
            guard.authorize(
                split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS,
                label_access_capability=wrong_capability,
            )

    def test_label_authorization_rejects_mutated_custody_receipt(self) -> None:
        guard = ProtocolExecutionGuardV1(self.protocol)
        guard.freeze_policies(self.receipt)
        guard.authorize(split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION)
        guard.record_development_prediction_frozen()
        capability, receipt_path = self.label_capability()
        receipt_path.write_bytes(receipt_path.read_bytes() + b" ")
        with self.assertRaisesRegex(PredictionCustodyError, "RECEIPT_MUTATED_AFTER_FREEZE"):
            guard.authorize(
                split_id="test1", operation=ProtocolOperationV1.DEVELOPMENT_LABEL_METRICS,
                label_access_capability=capability,
            )

    def test_protocol_has_explicit_failure_and_no_tuning_policy(self) -> None:
        self.assertTrue(self.protocol.no_post_test_tuning)
        self.assertTrue(self.protocol.prediction_before_label_required)
        self.assertEqual(self.protocol.failure_policy, "EXPLICIT_FAIL_CLOSED_NO_FAILURE_TO_NO_RULE_OR_NO_ALARM_COERCION")


if __name__ == "__main__":
    unittest.main()
