from __future__ import annotations

import copy
import unittest

from paperworks.v6.common import stable_hash_v1
from scripts import audit_task039e3_r2r_utility_inner_d1_result_integrity_v1 as audit


class IndependentInnerD1ResultIntegrityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = audit.repository_root_v1()
        cls.prediction = audit.load_public_json_v1(cls.root, audit.PUBLIC_JSON_PATHS["prediction"])
        cls.readiness = audit.load_public_json_v1(cls.root, audit.PUBLIC_JSON_PATHS["readiness"])
        cls.bundle = audit.load_public_json_v1(cls.root, audit.PUBLIC_JSON_PATHS["bundle"])
        cls.receipt = audit.load_public_json_v1(cls.root, audit.PUBLIC_JSON_PATHS["receipt"])

    @staticmethod
    def _rehash(document: dict[str, object]) -> dict[str, object]:
        document["artifact_hash"] = stable_hash_v1(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        return document

    def test_01_exact_frozen_public_audit_replays(self) -> None:
        self.assertTrue(audit.audit_git_freeze_v1(self.root)["result_freeze_commit_verified"])
        self.assertTrue(audit.audit_public_results_v1(self.root)["accounting_match"])

    def test_02_twenty_five_independent_rehashed_attacks_reject(self) -> None:
        attacks: list[tuple[dict[str, object], str]] = []
        fields = (
            ("authorization_hash", "0" * 64),
            ("bridge_identity", "1" * 64),
            ("execution_bridge_source_sha256", "2" * 64),
            ("execution_bridge_commit", "3" * 40),
            ("r3_implementation_identity", "4" * 64),
            ("evaluator_authority_bundle_hash", "5" * 64),
            ("v4_authority_hash", "6" * 64),
            ("main_private_registry_hash", "7" * 64),
            ("supplement_private_registry_hash", "8" * 64),
            ("feature_sha256", "9" * 64),
            ("split_identity", "a" * 64),
            ("common_relation_count", 41),
            ("common_portfolio", "T2"),
            ("scientific_eligible", False),
            ("label_blind", False),
        )
        for key, value in fields:
            document = copy.deepcopy(self.prediction)
            document[key] = value
            attacks.append((self._rehash(document), audit.PREDICTION_HASH))
        for container, key, value, expected in (
            (self.readiness, "committed_grant_hash", "b" * 64, audit.READINESS_HASH),
            (self.readiness, "execution_run_hash", "c" * 64, audit.READINESS_HASH),
            (self.bundle, "rule_prediction_artifact_hash", "d" * 64, audit.BUNDLE_HASH),
            (self.bundle, "private_metric_evidence_hash", "e" * 64, audit.BUNDLE_HASH),
            (self.receipt, "execution_attempts", 2, audit.RECEIPT_HASH),
            (self.receipt, "execution_retries", 1, audit.RECEIPT_HASH),
            (self.receipt, "test2_accesses", 1, audit.RECEIPT_HASH),
        ):
            document = copy.deepcopy(container)
            document[key] = value
            attacks.append((self._rehash(document), expected))
        for index, key, value in (
            (0, "trace_hash", "f" * 64),
            (0, "alarm_emitted", not self.prediction["prediction_records"][0]["alarm_emitted"]),
            (0, "decision_physical_row_index", -1),
        ):
            document = copy.deepcopy(self.prediction)
            document["prediction_records"][index][key] = value
            attacks.append((self._rehash(document), audit.PREDICTION_HASH))
        self.assertEqual(len(attacks), 25)
        accepted_invalid = 0
        for document, expected in attacks:
            try:
                audit.validate_self_hash_v1(document, expected)
            except audit.ResultIntegrityAuditV1Error:
                continue
            accepted_invalid += 1
        self.assertEqual(accepted_invalid, 0)

    def test_03_cross_authority_and_scope_escalation_reject_semantically(self) -> None:
        for key, value in (
            ("common_portfolio", "T2"),
            ("main_private_registry_hash", audit.SUPPLEMENT_REGISTRY_HASH),
            ("supplement_private_registry_hash", audit.MAIN_REGISTRY_HASH),
            ("execution_mode", "OUTER"),
        ):
            document = copy.deepcopy(self.prediction)
            document[key] = value
            self._rehash(document)
            with self.assertRaises(audit.ResultIntegrityAuditV1Error):
                audit.validate_prediction_semantics_v1(document)

    def test_04_result_files_remain_exact_commit_c_bytes(self) -> None:
        result = audit.audit_git_freeze_v1(self.root)
        self.assertEqual(result["post_freeze_mutation_count"], 0)
        self.assertFalse(result["bridge_changed_after_commit_a"])
        self.assertFalse(result["frozen_production_changed"])


if __name__ == "__main__":
    unittest.main()
