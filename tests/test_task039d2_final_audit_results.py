from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.profiling.task039d2_final_audit_v1 import (
    TASK039D2FinalAuditV1,
    TASK039E0AuthorizationV1,
    verify_audit_self_hash_v1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"


class TASK039D2FinalAuditResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads((REPORTS / "TASK-039D2_FINAL_AUDIT.json").read_text(encoding="utf-8"))
        cls.authorization = json.loads((REPORTS / "TASK-039E0_AUTHORIZATION.json").read_text(encoding="utf-8"))

    def test_result_hashes_schemas_and_closed_contracts(self) -> None:
        registry = load_v6_schema_registry_v1(repository_root=ROOT)
        for artifact_class, document in (
            (TASK039D2FinalAuditV1, self.audit),
            (TASK039E0AuthorizationV1, self.authorization),
        ):
            verify_audit_self_hash_v1(document)
            self.assertEqual(artifact_class.from_dict(document).to_dict(), document)
            validator = Draft202012Validator(registry.schema_for(document["artifact_type"]))
            self.assertEqual(list(validator.iter_errors(document)), [])

    def test_exact_replayed_scientific_partition_and_metrics(self) -> None:
        self.assertEqual(self.audit["status"], "passed_task039d2_final_audit")
        self.assertEqual(self.audit["readiness"], "READY_FOR_TASK039E0")
        self.assertEqual(self.audit["directional_partition"], {"confirmed": 42, "conflict": 3, "total": 45})
        self.assertEqual(self.audit["pair_reconstruction"]["confirmed_pairs"], 23)
        self.assertEqual(self.audit["pair_reconstruction"]["d1_supported_without_confirmation"], 2)
        expected = {
            "META": (15, 28, 7, 9),
            "STAT": (17, 32, 8, 8),
            "GDN": (3, 5, 3, 3),
        }
        for arm, (pairs, directions, sources, targets) in expected.items():
            self.assertEqual(self.audit["arm_metrics"][arm]["confirmed_pairs"], pairs)
            self.assertEqual(self.audit["arm_metrics"][arm]["confirmed_directions"], directions)
            self.assertEqual(self.audit["coverage"][arm]["confirmed_source_count"], sources)
            self.assertEqual(self.audit["coverage"][arm]["confirmed_target_count"], targets)
        self.assertEqual(self.audit["confirmed_pair_overlap"]["confirmed_union"], 23)
        self.assertEqual(self.audit["confirmed_pair_overlap"]["exactly_two"], 12)

    def test_arm_blind_no_retuning_and_data_boundaries(self) -> None:
        self.assertTrue(self.audit["arm_blindness"]["same_pair_same_d2_outcome_across_all_origin_arms"])
        self.assertFalse(any(self.audit["no_retuning"].values()))
        boundary = self.audit["data_boundaries"]
        self.assertTrue(boundary["original"]["train3"])
        self.assertFalse(boundary["recovery"]["train3_reread"])
        self.assertTrue(boundary["audit"]["train3"])
        for field in ("train1", "train2", "train4", "test", "labels", "attacks", "p2_p3_p4", "br2_pair_results"):
            self.assertFalse(boundary["audit"][field])

    def test_e0_is_protocol_design_only(self) -> None:
        self.assertEqual(self.authorization["confirmed_directional_count"], 42)
        self.assertEqual(self.authorization["confirmed_pair_count"], 23)
        for field in (
            "real_rule_generation_authorized", "llm_calls_authorized",
            "t0_generation_authorized", "t1_t1b_t2_generation_authorized",
            "rule_v2_runtime_authorized", "agent_execution_authorized",
            "detector_integration_authorized", "train4_authorized",
            "test_labels_attacks_authorized", "outer_sealed_evaluation_authorized",
        ):
            self.assertFalse(self.authorization[field], field)

    def test_public_outputs_contain_no_absolute_paths_or_private_contents(self) -> None:
        for name in ("TASK-039D2_FINAL_AUDIT.json", "TASK-039E0_AUTHORIZATION.json", "TASK-039D2_FINAL_AUDIT.md"):
            text = (REPORTS / name).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]", text), name)
            self.assertNotIn("TASK039D2_AUDIT_PRIVATE_REPLAY_LEDGER", text)
            self.assertNotIn("event_index", text)


if __name__ == "__main__":
    unittest.main()
