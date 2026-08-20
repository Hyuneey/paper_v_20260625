from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import numpy as np

from scripts import audit_task039e3_r2r_d0_result_integrity_v1 as audit


class TestD0ResultIntegrityAuditV1(unittest.TestCase):
    def test_frozen_semantic_identities_replay(self) -> None:
        self.assertEqual(
            audit.independent_implementation_identity_v1(),
            audit.EXECUTION_IMPLEMENTATION_IDENTITY,
        )
        self.assertEqual(
            audit.stable_hash_v1(audit.expected_grant_payload_v1()),
            audit.COMMITTED_GRANT_HASH,
        )

    def test_self_hash_rejects_rehashless_mutation(self) -> None:
        document = audit.self_hashed_v1({"artifact_type": "synthetic", "value": 1})
        audit.validate_self_hash_v1(document)
        document["value"] = 2
        with self.assertRaises(audit.D0ResultIntegrityAuditError):
            audit.validate_self_hash_v1(document)

    def test_prediction_fixture_has_exact_closure_and_label_blind_schema(self) -> None:
        document = audit.synthetic_prediction_v1(8)
        count, indices = audit.validate_prediction_document_v1(
            document, expected_count=8, expected_artifact_hash=document["artifact_hash"]
        )
        self.assertEqual(count, 4)
        self.assertEqual(indices, (1, 3, 5, 7))
        self.assertTrue(all(set(record) == audit.RECORD_KEYS for record in document["prediction_records"]))

    def test_prediction_rejects_inserted_sensitive_fields_even_when_rehashed(self) -> None:
        for field, value in (
            ("label", 1), ("attack", True), ("score", 1.0), ("threshold", 1.0)
        ):
            with self.subTest(field=field):
                document = audit.synthetic_prediction_v1(8)
                document["prediction_records"][0][field] = value
                audit._rehash_v1(document)
                with self.assertRaises(audit.D0ResultIntegrityAuditError):
                    audit.validate_prediction_document_v1(
                        document, expected_count=8, expected_artifact_hash=None
                    )

    def test_independent_score_oracle_matches_manual_residual_spe(self) -> None:
        matrix = np.zeros((audit.EXPECTED_ROWS, audit.FEATURE_COUNT), dtype=np.float64)
        matrix[0, 10] = 3.0
        matrix[1, 11] = 4.0
        means = np.zeros(audit.FEATURE_COUNT, dtype=np.float64)
        scales = np.ones(audit.FEATURE_COUNT, dtype=np.float64)
        loadings = np.zeros((audit.FEATURE_COUNT, audit.SELECTED_K), dtype=np.float64)
        loadings[: audit.SELECTED_K, :] = np.eye(audit.SELECTED_K, dtype=np.float64)
        scores = audit.independent_score_oracle_v1(matrix, means, scales, loadings)
        self.assertEqual(float(scores[0]), 9.0)
        self.assertEqual(float(scores[1]), 16.0)
        self.assertTrue(np.all(scores[2:] == 0.0))

    def test_strict_threshold_equality_is_not_alarm(self) -> None:
        scores = np.asarray([1.0, 1.5, 2.0], dtype=np.float64)
        alarms = scores > np.float64(1.5)
        self.assertEqual(alarms.tolist(), [False, False, True])

    def test_alarm_episode_oracle_is_maximal_sorted_and_unique(self) -> None:
        self.assertEqual(
            audit.form_alarm_episodes_v1((4, 2, 3, 3, 9, 11, 10)),
            ((2, 5), (9, 12)),
        )

    def test_attack_event_oracle_uses_strict_contiguous_one_runs(self) -> None:
        self.assertEqual(
            audit.derive_attack_events_v1((0, 1, 1, 0, 1, 0, 0, 1)),
            ((1, 3), (4, 5), (7, 8)),
        )

    def test_local_commit_missing_is_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            audit.D0ResultIntegrityAuditError,
            "D0_RESULT_INTEGRITY_BLOCKED_LOCAL_COMMIT_MISSING",
        ):
            audit.validate_commit_resolution_v1(
                lambda commit: commit != audit.RESULT_FREEZE_COMMIT_C
            )

    def test_wrong_frozen_bytes_are_rejected(self) -> None:
        with self.assertRaises(audit.D0ResultIntegrityAuditError):
            audit.validate_equal_bytes_v1(b"current", b"frozen")

    def test_execution_source_has_prediction_before_label_controls_and_no_retry_loop(self) -> None:
        source = (Path(__file__).parents[1] / audit.EXECUTION_SOURCE).read_bytes()
        controls = audit.audit_execution_control_structure_v1(source)
        self.assertTrue(all(controls.values()))

    def test_authorization_and_public_result_documents_validate(self) -> None:
        root = Path(__file__).parents[1]
        authorization = json.loads((root / audit.AUTHORIZATION_PATHS["authorization"]).read_text())
        prediction = json.loads((root / audit.PREDICTION_PATH).read_text())
        metrics = json.loads((root / audit.METRICS_PATH).read_text())
        accounting = json.loads((root / audit.ACCOUNTING_PATH).read_text())
        audit.validate_authorization_document_v1(authorization)
        audit.validate_prediction_document_v1(prediction)
        audit.validate_metrics_document_v1(metrics)
        audit.validate_accounting_document_v1(accounting)

    def test_accounting_retry_and_boundary_mutations_reject(self) -> None:
        root = Path(__file__).parents[1]
        original = json.loads((root / audit.ACCOUNTING_PATH).read_text())
        for key, value in (
            ("scientific_execution_retries", 1),
            ("label_before_prediction_access", True),
            ("D1_content_reads", 1),
            ("D2_executions", 1),
            ("test2_accesses", 1),
            ("result_driven_changes", True),
        ):
            with self.subTest(key=key):
                document = copy.deepcopy(original)
                document[key] = value
                audit._rehash_v1(document)
                with self.assertRaises(audit.D0ResultIntegrityAuditError):
                    audit.validate_accounting_document_v1(document)


if __name__ == "__main__":
    unittest.main()
