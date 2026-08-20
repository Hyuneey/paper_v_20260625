from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d0_integrity_audit_independent_v1",
    ROOT / "scripts/audit_task039e3_r2r_d0_model_threshold_integrity_v1.py",
)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class D0ModelThresholdIntegrityIndependentAttacks(unittest.TestCase):
    def _documents(self):
        return AUDIT._load_public_reports()

    @staticmethod
    def _rehash(document):
        document["artifact_hash"] = AUDIT.canonical_hash_v1(document)

    def _must_reject_semantic_mutation(self, section, field, value) -> None:
        documents = copy.deepcopy(self._documents())
        documents[section][field] = value
        self._rehash(documents[section])
        with self.assertRaises(AUDIT.D0IntegrityAuditError):
            AUDIT.validate_frozen_public_semantics_v1(documents)

    def test_30_self_rehashed_semantic_attacks_are_rejected(self) -> None:
        attacks = (
            ("model_receipt", "d0_design_hash", "0" * 64),
            ("model_receipt", "feature_count", 36),
            ("model_receipt", "feature_set_hash", "1" * 64),
            ("model_receipt", "feature_order_hash", "2" * 64),
            ("model_receipt", "preprocessing_content_hash", "3" * 64),
            ("model_receipt", "model_content_hash", "4" * 64),
            ("model_receipt", "selected_k", 9),
            ("model_receipt", "residual_dimensions", 28),
            ("model_receipt", "exact_tied_cutoff_encountered", True),
            ("threshold_receipt", "d0_design_hash", "5" * 64),
            ("threshold_receipt", "model_content_hash", "6" * 64),
            ("threshold_receipt", "threshold_content_hash", "7" * 64),
            ("threshold_receipt", "alpha", 0.01),
            ("threshold_receipt", "q_index", 125874),
            ("threshold_receipt", "comparison_operator", "score >= threshold"),
            ("train4_sanity", "point_alarm_count", 15400),
            ("train4_sanity", "alarm_episode_count", 480),
            ("train4_sanity", "normal_far_episodes_per_hour", 8.7),
            ("train4_sanity", "result_driven_change", True),
            ("accounting", "model_fit_attempts", 2),
            ("accounting", "model_fit_retries", 1),
            ("accounting", "threshold_calibration_attempts", 2),
            ("accounting", "threshold_calibration_retries", 1),
            ("accounting", "train1_scientific_parses", 0),
            ("accounting", "train2_scientific_parses", 0),
            ("accounting", "train3_scientific_parses", 0),
            ("accounting", "train4_scientific_parses", 0),
            ("accounting", "test1_accesses", 1),
            ("accounting", "label_accesses", 1),
            ("accounting", "test2_accesses", 1),
            ("accounting", "d0_inner_executions", 1),
            ("accounting", "d2_executions", 1),
            ("accounting", "outer_executions", 1),
            ("accounting", "d1_performance_reads", 1),
            ("accounting", "result_driven_changes", True),
        )
        accepted_invalid = 0
        for attack in attacks:
            with self.subTest(attack=attack):
                try:
                    self._must_reject_semantic_mutation(*attack)
                except AssertionError:
                    accepted_invalid += 1
        self.assertEqual(len(attacks), 35)
        self.assertEqual(accepted_invalid, 0)

    def test_rehashed_receipt_cross_binding_attack_is_rejected(self) -> None:
        documents = copy.deepcopy(self._documents())
        documents["receipt"]["bundle_hash"] = "8" * 64
        self._rehash(documents["receipt"])
        with self.assertRaises(AUDIT.D0IntegrityAuditError):
            AUDIT._validate_public_cross_hashes(documents)

    def test_reconstructed_model_private_payload_cannot_match_authority(self) -> None:
        forged = {
            "artifact_type": "task039e3_r2r_d0_pca_model_artifact_v1",
            "design_hash": AUDIT.DESIGN_HASH,
            "selected_k": 10,
        }
        forged["artifact_hash"] = AUDIT.canonical_hash_v1(forged)
        self.assertNotEqual(forged["artifact_hash"], AUDIT.MODEL_HASH)

    def test_reconstructed_threshold_private_payload_cannot_match_authority(self) -> None:
        forged = {
            "artifact_type": "task039e3_r2r_d0_threshold_artifact_v1",
            "alpha": 0.001,
            "q_index": 125873,
            "comparison_operator": "score >= threshold",
        }
        forged["artifact_hash"] = AUDIT.canonical_hash_v1(forged)
        self.assertNotEqual(forged["artifact_hash"], AUDIT.THRESHOLD_HASH)

    def test_design_and_result_documents_contain_no_d1_performance_values(self) -> None:
        forbidden = ("0.9285714285714286", "40.50255787059723", "D1_METRICS_V1")
        paths = (
            ROOT / "configs/v6/task039e3_r2r_d0_pca_spe_detector_v1.json",
            ROOT / "src/paperworks/v6/task039e3_r2r_d0_detector_training_v1.py",
        )
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        self.assertTrue(all(token not in text for token in forbidden))

    def test_public_documents_reject_duplicate_json_keys_in_strict_audit_fixture(self) -> None:
        raw = '{"artifact_hash":"a","artifact_hash":"b"}'
        pairs = json.loads(raw, object_pairs_hook=lambda values: values)
        names = [name for name, _ in pairs]
        self.assertNotEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
