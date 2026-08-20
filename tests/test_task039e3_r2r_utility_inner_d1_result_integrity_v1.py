from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from paperworks.v6.common import stable_hash_v1
from scripts import audit_task039e3_r2r_utility_inner_d1_result_integrity_v1 as audit


class InnerD1ResultIntegrityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = audit.repository_root_v1()
        cls.prediction = audit.load_public_json_v1(cls.root, audit.PUBLIC_JSON_PATHS["prediction"])
        cls.metrics = audit.load_public_json_v1(cls.root, audit.PUBLIC_JSON_PATHS["metrics"])
        cls.accounting = audit.load_public_json_v1(cls.root, audit.PUBLIC_JSON_PATHS["accounting"])

    @staticmethod
    def _rehash(document: dict[str, object]) -> dict[str, object]:
        document["artifact_hash"] = stable_hash_v1(
            {key: value for key, value in document.items() if key != "artifact_hash"}
        )
        return document

    def test_01_git_freeze_and_public_graph_pass(self) -> None:
        freeze = audit.audit_git_freeze_v1(self.root)
        self.assertTrue(freeze["result_freeze_commit_verified"])
        self.assertEqual(freeze["post_freeze_mutation_count"], 0)
        grant = audit.audit_authorization_and_grant_v1(self.root)
        self.assertTrue(grant["committed_grant_match"])
        public = audit.audit_public_results_v1(self.root)
        self.assertEqual(public["prediction_record_count"], 6031)
        self.assertEqual(public["alarm_episode_oracle_count"], 626)

    def test_02_prediction_exact_structure_and_trace_closure(self) -> None:
        result = audit.validate_frozen_prediction_v1(self.prediction)
        self.assertEqual(result["prediction_record_count"], 6031)
        self.assertEqual(result["unique_opportunity_count"], 6031)
        self.assertEqual(result["trace_count"], 6031)
        self.assertEqual(result["alarm_count"], 788)
        self.assertTrue(result["label_blind_schema_pass"])

    def test_03_alarm_oracle_is_label_blind_and_exact(self) -> None:
        episodes = audit.form_alarm_episodes_v1(self.prediction)
        self.assertEqual(len(episodes), 626)
        self.assertTrue(all(type(start) is int and type(end) is int and start < end for start, end in episodes))

    def test_04_twenty_prediction_mutations_and_self_rehash_reject(self) -> None:
        attacks = []

        def mutate_record(index: int, key: str, value: object) -> dict[str, object]:
            document = copy.deepcopy(self.prediction)
            document["prediction_records"][index][key] = value
            return self._rehash(document)

        deleted = copy.deepcopy(self.prediction)
        deleted["prediction_records"].pop()
        attacks.append(self._rehash(deleted))
        inserted = copy.deepcopy(self.prediction)
        inserted["prediction_records"].append(copy.deepcopy(inserted["prediction_records"][0]))
        attacks.append(self._rehash(inserted))
        reordered = copy.deepcopy(self.prediction)
        reordered["prediction_records"][0], reordered["prediction_records"][1] = reordered["prediction_records"][1], reordered["prediction_records"][0]
        attacks.append(self._rehash(reordered))
        duplicate = copy.deepcopy(self.prediction)
        duplicate["prediction_records"][1] = copy.deepcopy(duplicate["prediction_records"][0])
        attacks.append(self._rehash(duplicate))
        attacks.extend(
            (
                mutate_record(0, "alarm_emitted", not self.prediction["prediction_records"][0]["alarm_emitted"]),
                mutate_record(0, "final_state", "abstain"),
                mutate_record(0, "decision_physical_row_index", 53999),
                mutate_record(0, "trace_hash", "0" * 64),
                mutate_record(0, "computation_identity", "1" * 64),
                mutate_record(0, "opportunity_id", "2" * 64),
                mutate_record(0, "source_event_identity_hash", "3" * 64),
                mutate_record(0, "relation_binding_hash", "4" * 64),
                mutate_record(0, "numeric_reference_identities", ["TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1:" + "5" * 64] * 10),
            )
        )
        for key, value in (
            ("authorization_hash", "6" * 64),
            ("bridge_identity", "7" * 64),
            ("execution_bridge_commit", "8" * 40),
            ("main_private_registry_hash", "9" * 64),
            ("supplement_private_registry_hash", "a" * 64),
            ("feature_sha256", "b" * 64),
            ("label_blind", False),
        ):
            document = copy.deepcopy(self.prediction)
            document[key] = value
            attacks.append(self._rehash(document))
        self.assertEqual(len(attacks), 20)
        for document in attacks:
            with self.assertRaises(audit.ResultIntegrityAuditV1Error):
                audit.validate_frozen_prediction_v1(document)

    def test_05_forbidden_prediction_fields_reject_semantically(self) -> None:
        for key in ("label", "attack_interval", "numeric_value", "raw_feature_values"):
            document = copy.deepcopy(self.prediction)
            document["prediction_records"][0][key] = 1
            self._rehash(document)
            with self.assertRaises(audit.ResultIntegrityAuditV1Error):
                audit.validate_prediction_semantics_v1(document)

    def test_06_metric_and_accounting_frozen_hash_attacks_reject(self) -> None:
        attacks: list[tuple[dict[str, object], str]] = []
        metric_value = copy.deepcopy(self.metrics)
        metric_value["attack_event_recall"]["value"] = 0.0
        attacks.append((self._rehash(metric_value), audit.METRICS_HASH))
        metric_formula = copy.deepcopy(self.metrics)
        metric_formula["normal_far_episodes_per_hour"]["formula_identity"] = "FORGED"
        attacks.append((self._rehash(metric_formula), audit.METRICS_HASH))
        attempts = copy.deepcopy(self.accounting)
        attempts["scientific_execution_attempts"] = 2
        attacks.append((self._rehash(attempts), audit.ACCOUNTING_HASH))
        retries = copy.deepcopy(self.accounting)
        retries["scientific_execution_retries"] = 1
        attacks.append((self._rehash(retries), audit.ACCOUNTING_HASH))
        changed = copy.deepcopy(self.accounting)
        changed["result_driven_changes"] = True
        attacks.append((self._rehash(changed), audit.ACCOUNTING_HASH))
        for document, expected in attacks:
            with self.assertRaises(audit.ResultIntegrityAuditV1Error):
                audit.validate_self_hash_v1(document, expected)

    def test_07_audit_code_cannot_call_real_d1_or_rule_execution(self) -> None:
        source = Path(audit.__file__).read_text(encoding="utf-8")
        forbidden_calls = (
            "execute_authorized_inner_d1_v1(",
            "execute_real_rule_v1(",
            "run_real_utility_evaluator_v1(",
        )
        for call in forbidden_calls:
            self.assertNotIn(call, source)

    def test_08_bridge_enforces_prediction_before_label_and_single_attempt(self) -> None:
        source = (self.root / "src/paperworks/v6/task039e3_r2r_utility_inner_d1_execution_v1.py").read_text(encoding="utf-8")
        prediction_call = source.index("prediction = build_scientific_rule_prediction_artifact_v1(")
        label_call = source.index("label_custody = _load_real_label_custody_v1(")
        self.assertLess(prediction_call, label_call)
        self.assertIn("if _SCIENTIFIC_EXECUTION_ATTEMPTS != 0 or _SCIENTIFIC_EXECUTION_COMPLETED:", source)
        self.assertNotIn("scientific_execution_retries +=", source)


if __name__ == "__main__":
    unittest.main()
