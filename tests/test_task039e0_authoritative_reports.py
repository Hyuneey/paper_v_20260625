from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import jsonschema

from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1
from paperworks.v6.task039e0_rule_construction_protocol_v1 import verify_self_hash_v1


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = {
    "confirmed_relation_identity_cohort_v1": "TASK-039E0_CONFIRMED_RELATION_COHORT.json",
    "fair_generation_budget_policy_v2": "TASK-039E0_BUDGET_POLICY.json",
    "t1b_selection_policy_v1": "TASK-039E0_T1B_SELECTION_POLICY.json",
    "t2_deterministic_controller_policy_v1": "TASK-039E0_CONTROLLER_POLICY.json",
    "task039e0_validity_policy_v2": "TASK-039E0_VALIDITY_POLICY.json",
    "construction_evidence_materialization_policy_v1": "TASK-039E0_EVIDENCE_MATERIALIZATION_POLICY.json",
    "llm_direct_number_evaluation_policy_v1": "TASK-039E0_DIRECT_NUMBER_POLICY.json",
    "construction_metric_policy_v1": "TASK-039E0_CONSTRUCTION_METRIC_POLICY.json",
    "task039e0_protocol_bundle_v1": "TASK-039E0_PROTOCOL_BUNDLE.json",
    "task039e1_authorization_v1": "TASK-039E1_AUTHORIZATION.json",
}


class AuthoritativeReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_v6_schema_registry_v1(repository_root=ROOT)

    def test_registry_contains_prep_and_authoritative_schemas(self) -> None:
        self.assertEqual(len(self.registry.artifact_types), 144)
        for artifact_type in (*ARTIFACTS, "task039e0_prepared_validity_result_v2"):
            self.assertIn(artifact_type, self.registry.artifact_types)
        self.assertNotIn("fair_generation_budget_policy_v1", self.registry.artifact_types)

    def test_all_public_artifacts_self_hash_and_validate(self) -> None:
        for artifact_type, filename in ARTIFACTS.items():
            with self.subTest(artifact_type=artifact_type):
                document = json.loads((ROOT / "docs" / "task_reports" / filename).read_text(encoding="utf-8"))
                self.assertTrue(verify_self_hash_v1(document))
                jsonschema.Draft202012Validator(
                    self.registry.schema_for(artifact_type),
                    format_checker=jsonschema.FormatChecker(),
                ).validate(document)

    def test_unknown_fields_are_rejected(self) -> None:
        artifact_type = "fair_generation_budget_policy_v2"
        document = json.loads((ROOT / "docs" / "task_reports" / ARTIFACTS[artifact_type]).read_text(encoding="utf-8"))
        mutated = copy.deepcopy(document)
        mutated["unexpected"] = True
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(mutated, self.registry.schema_for(artifact_type))

    def test_protocol_bundle_has_no_execution_authority(self) -> None:
        document = json.loads((ROOT / "docs" / "task_reports" / ARTIFACTS["task039e0_protocol_bundle_v1"]).read_text(encoding="utf-8"))
        self.assertEqual(document["status"], "passed_task039e0_rule_construction_protocol_freeze")
        self.assertTrue(document["real_d2_result_consumed"])
        self.assertFalse(document["d1_d2_private_ledgers_accessed"])
        self.assertFalse(document["hai_accessed"])
        self.assertFalse(document["llm_called"])
        self.assertFalse(document["t0_generated"])
        self.assertFalse(document["t1_t1b_t2_generated"])
        self.assertFalse(document["rule_v2_created"])
        self.assertEqual(document["arm_protocols"]["T1-B"]["generation_calls"], 3)
        self.assertEqual(document["arm_protocols"]["T2"]["maximum_generation_calls"], 3)
        self.assertFalse(document["no_rule_semantics"]["transport_failure"])
        self.assertTrue(document["future_model_execution_freeze"]["required_before_any_real_llm_call"])
        self.assertTrue(document["relation_inclusion_policy"]["all_42_confirmed_directional_relations_eligible"])
        self.assertFalse(document["relation_inclusion_policy"]["candidate_origin_filtering"])

    def test_generation_is_deterministic(self) -> None:
        before = {
            filename: (ROOT / "docs" / "task_reports" / filename).read_bytes()
            for filename in ARTIFACTS.values()
        }
        from scripts.freeze_task039e0_rule_construction_protocol import freeze
        freeze(ROOT)
        after = {
            filename: (ROOT / "docs" / "task_reports" / filename).read_bytes()
            for filename in ARTIFACTS.values()
        }
        self.assertEqual(before, after)

    def test_protocol_implementation_has_no_data_or_private_loader(self) -> None:
        files = (
            ROOT / "src/paperworks/v6/task039e0_rule_construction_protocol_v1.py",
            ROOT / "src/paperworks/v6/task039e0_validity_v2.py",
            ROOT / "scripts/freeze_task039e0_rule_construction_protocol.py",
        )
        prohibited = (
            "HAI_DATA_ROOT", "TASK039D_PRIVATE_ROOT", "TASK039D2_PRIVATE_ROOT",
            "load_authorized_train", "read_csv", "pandas", "confirm_relations_one_way_v1",
        )
        for path in files:
            text = path.read_text(encoding="utf-8")
            for marker in prohibited:
                self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
