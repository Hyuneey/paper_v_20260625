from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from paperworks.candidates.candidate_integration_v1 import (
    CandidateProfilingCohortV1,
    TASK039CIntegrationReceiptV1,
    TASK039CThreeArmOverlapV1,
    TASK039D0AuthorizationV1,
    stable_hash_v1,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "task_reports"
COMMIT_A = "75a4899ba67e067a88dd363d9bb90554add82cf2"
ARTIFACTS = {
    "TASK-039C_THREE_ARM_OVERLAP.json": ("task039c_three_arm_overlap_v1_schema.json", TASK039CThreeArmOverlapV1),
    "TASK-039C_CANDIDATE_PROFILING_COHORT.json": ("candidate_profiling_cohort_v1_schema.json", CandidateProfilingCohortV1),
    "TASK-039C_INTEGRATION_RECEIPT.json": ("task039c_integration_receipt_v1_schema.json", TASK039CIntegrationReceiptV1),
    "TASK-039D0_AUTHORIZATION.json": ("task039d0_authorization_v1_schema.json", TASK039D0AuthorizationV1),
}


def read(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


class Task039CIntegrationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.overlap = read("TASK-039C_THREE_ARM_OVERLAP.json")
        cls.cohort = read("TASK-039C_CANDIDATE_PROFILING_COHORT.json")
        cls.receipt = read("TASK-039C_INTEGRATION_RECEIPT.json")
        cls.authorization = read("TASK-039D0_AUTHORIZATION.json")

    def test_artifacts_validate_schema_and_contract_self_hash(self) -> None:
        for name, (schema_name, contract) in ARTIFACTS.items():
            with self.subTest(name=name):
                document = read(name)
                schema = json.loads((ROOT / "schemas" / "v6" / schema_name).read_text(encoding="utf-8"))
                Draft202012Validator(schema).validate(document)
                parsed = contract.from_dict(document)
                self.assertEqual(parsed.artifact_hash, document["artifact_hash"])

    def test_every_nested_candidate_and_arm_binding_self_hashes(self) -> None:
        for item in self.cohort["candidates"] + self.cohort["arm_bindings"]:
            supplied = item["artifact_hash"]
            payload = dict(item)
            payload.pop("artifact_hash")
            self.assertEqual(supplied, stable_hash_v1(payload))

    def test_execution_commit_is_exact_commit_a(self) -> None:
        self.assertEqual(self.receipt["integration_execution_code_commit"], COMMIT_A)
        completed = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", COMMIT_A, "HEAD"], check=False)
        self.assertEqual(completed.returncode, 0)

    def test_result_hashes_and_preview_are_exact(self) -> None:
        self.assertEqual(self.receipt["result_artifact_hashes"], {
            "META": "0e3b055df911c74bd0e0993b7b3bb122860b265192ad0cf91d54edc1e74635bf",
            "STAT": "7351e295be7e5bdd2b1cb9677091426899e5a2616c60245f953ff6602d106950",
            "GDN": "2c58308d0d97d93cf671907064c805dbadcb01508ed8571090a448be6c855bfc",
        })
        self.assertEqual(self.receipt["audited_preview_hash"], "81a7b6e0dfffdd6ce1b49799721c3dfcfb484af247a194d87b0602e76ac551ff")

    def test_final_cohort_and_origin_decomposition(self) -> None:
        self.assertEqual(self.cohort["union_count"], 47)
        self.assertEqual(self.cohort["origin_decomposition"], {"META_only": 8, "STAT_only": 8, "GDN_only": 18, "META_STAT_only": 11, "META_GDN_only": 1, "STAT_GDN_only": 1, "all_three": 0})
        identities = [(x["source"], x["target"]) for x in self.cohort["candidates"]]
        self.assertEqual(len(identities), len(set(identities)))

    def test_artifact_cross_bindings_are_exact(self) -> None:
        self.assertEqual(self.receipt["candidate_cohort_hash"], self.cohort["artifact_hash"])
        self.assertEqual(self.receipt["overlap_artifact_hash"], self.overlap["artifact_hash"])
        self.assertEqual(self.receipt["task039d0_authorization_hash"], self.authorization["artifact_hash"])
        self.assertEqual(self.authorization["candidate_cohort_hash"], self.cohort["artifact_hash"])

    def test_no_global_rank_or_merged_score(self) -> None:
        self.assertFalse(self.receipt["merged_score_created"] or self.receipt["global_rank_created"])
        for candidate in self.cohort["candidates"]:
            self.assertIsNone(candidate["global_rank"])
            self.assertIsNone(candidate["global_score"])
            self.assertFalse(candidate["serialization_order_is_scientific_rank"])

    def test_public_authority_boundaries(self) -> None:
        self.assertFalse(self.receipt["hai_feature_access"])
        self.assertFalse(self.receipt["private_ledger_access"])
        self.assertFalse(self.receipt["br2_ground_truth_used"])
        self.assertTrue(self.authorization["protocol_design_authorized"])
        for key, value in self.authorization.items():
            if key.endswith("authorized") and key != "protocol_design_authorized":
                self.assertFalse(value)

    def test_public_outputs_contain_no_absolute_paths_or_private_payloads(self) -> None:
        absolute = re.compile(r"(?:[A-Za-z]:[\\/]|/home/|/Users/|\\\\[^\\]+\\[^\\]+)")
        prohibited = ("raw_rows", "raw_windows", "private_ledger_contents", "state_dict", "attack_details")
        for name in (*ARTIFACTS, "TASK-039C_REPORT.md"):
            text = (REPORTS / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIsNone(absolute.search(text))
                for token in prohibited:
                    self.assertNotIn(token, text)

    def test_report_states_completed_boundary(self) -> None:
        report = (REPORTS / "TASK-039C_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("passed_task039c_three_arm_candidate_cohort_freeze", report)
        self.assertIn("TASK-039D0", report)
        self.assertIn("remain unauthorized", report)


if __name__ == "__main__":
    unittest.main()
