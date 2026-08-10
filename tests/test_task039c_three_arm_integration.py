from __future__ import annotations

import copy
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from paperworks.candidates.candidate_integration_v1 import (
    CandidateIntegrationError,
    CandidateProfilingCohortV1,
    CandidateProfilingEntryV1,
    EXPECTED_PREVIEW_HASH,
    TASK039CArmBindingV1,
    TASK039CIntegrationReceiptV1,
    TASK039CThreeArmOverlapV1,
    TASK039D0AuthorizationV1,
    assert_public_payload_v1,
    build_task039c_integration_v1,
    load_merged_public_inputs_v1,
    reconstruct_audited_preview_v1,
    stable_hash_v1,
)
from paperworks.v6.schema_registry_v1 import load_v6_schema_registry_v1


ROOT = Path(__file__).resolve().parents[1]
EXECUTION_PLACEHOLDER = "2c9d9f7989258f02e85e7a201f56a844d76fc8e7"
ANCESTORS = (
    "b6522fb83c4cb92d355f98af778f9a6a3c73362f",
    "2b3df4443619b8d0d19434bbcd1ded3b31a1b8ea",
    "b8a744c4b2cc70cd70bfc73ce45408c2ec8b5824",
    "629f022d35bb0db6130e7e69faaf48408b49aa9a",
    "9359a8b8085b1948bde23171ec886e996fbd37b3",
    "058b5e2023b66ccbf6704c5baf1f6c677f17b07a",
    "6790505e08ea06d6b3f6d34f9fd533d381696b1f",
    "1204ff4e6d790c2cd0e8268f778a8f071e5eea4b",
    "eab10dee0f08f419638154a9902304339b63c471",
)


class Task039CThreeArmIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inputs = load_merged_public_inputs_v1(ROOT)
        cls.result = build_task039c_integration_v1(
            **cls.inputs,
            integration_execution_code_commit=EXECUTION_PLACEHOLDER,
        )

    def test_exact_historical_commits_are_ancestors(self) -> None:
        for commit in ANCESTORS:
            with self.subTest(commit=commit):
                completed = subprocess.run(
                    ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
                    check=False,
                )
                self.assertEqual(completed.returncode, 0)

    def test_public_input_allowlist_has_exact_six_files(self) -> None:
        self.assertEqual(set(self.inputs), {"c0_bundle", "meta_result", "stat_result", "gdn_result", "preliminary_review", "final_gdn_audit"})

    def test_audited_preview_hash_reconstructed(self) -> None:
        preview = reconstruct_audited_preview_v1(
            universe_hash=self.inputs["c0_bundle"]["universe_policy"]["eligible_pair_universe_hash"],
            meta_result=self.inputs["meta_result"], stat_result=self.inputs["stat_result"], gdn_result=self.inputs["gdn_result"],
        )
        self.assertEqual(stable_hash_v1(preview), EXPECTED_PREVIEW_HASH)
        self.assertEqual(preview, self.inputs["final_gdn_audit"]["provisional_preview"])

    def test_frozen_helper_is_invoked_once(self) -> None:
        import paperworks.candidates.candidate_integration_v1 as module
        original = module.integrate_candidate_union_v1
        with patch.object(module, "integrate_candidate_union_v1", wraps=original) as helper:
            build_task039c_integration_v1(**self.inputs, integration_execution_code_commit=EXECUTION_PLACEHOLDER)
        helper.assert_called_once()

    def test_primary_overlap_is_exact(self) -> None:
        self.assertEqual(self.result.overlap.top20.to_dict(), {
            "meta_count": 20, "stat_count": 20, "gdn_count": 20,
            "meta_stat": 11, "meta_gdn": 1, "stat_gdn": 1, "triple": 0,
            "meta_only": 8, "stat_only": 8, "gdn_only": 18,
            "meta_stat_only": 11, "meta_gdn_only": 1, "stat_gdn_only": 1,
            "all_three": 0, "union_count": 47,
        })

    def test_top10_overlap_and_identities_are_exact(self) -> None:
        self.assertEqual(self.result.overlap.top10.union_count, 28)
        self.assertEqual(self.result.overlap.top10_meta_stat_only_pairs, (("P1_FCV01D", "P1_FT02Z"),))
        self.assertEqual(self.result.overlap.top10_meta_gdn_only_pairs, (("P1_FCV02D", "P1_TIT01"),))
        self.assertEqual(self.result.overlap.top10_stat_gdn_only_pairs, ())

    def test_sensitivity_is_unpadded_and_nonprimary(self) -> None:
        overlap = self.result.overlap
        self.assertEqual(overlap.sensitivity.union_count, 76)
        self.assertEqual((overlap.sensitivity.meta_only, overlap.sensitivity.stat_only, overlap.sensitivity.gdn_only), (2, 14, 30))
        self.assertFalse(overlap.meta_padded or overlap.gdn_padded or overlap.sensitivity_is_primary_cohort)

    def test_cohort_has_47_unique_in_universe_pairs(self) -> None:
        identities = self.result.cohort.candidate_identity_list
        self.assertEqual(len(identities), 47)
        self.assertEqual(len(set(identities)), 47)
        universe = self.inputs["c0_bundle"]["universe_policy"]
        allowed = {(a, b) for a in universe["source_variables"] for b in universe["target_variables"]}
        self.assertLessEqual(set(identities), allowed)

    def test_serialization_is_not_scientific_rank(self) -> None:
        for position, entry in enumerate(self.result.cohort.candidates, start=1):
            self.assertEqual(entry.serialization_position, position)
            self.assertIsNone(entry.global_rank)
            self.assertIsNone(entry.global_score)
            self.assertFalse(entry.serialization_order_is_scientific_rank)

    def test_origin_arms_exactly_match_method_evidence(self) -> None:
        for entry in self.result.cohort.candidates:
            evidence = {"META": entry.meta_evidence, "STAT": entry.stat_evidence, "GDN": entry.gdn_evidence}
            for arm, value in evidence.items():
                self.assertEqual(arm in entry.origin_arms, value is not None)

    def test_method_specific_values_are_preserved(self) -> None:
        meta = next(x for x in self.result.cohort.candidates if x.meta_evidence)
        stat = next(x for x in self.result.cohort.candidates if x.stat_evidence)
        gdn = next(x for x in self.result.cohort.candidates if x.gdn_evidence)
        self.assertIn("evidence_tier", meta.meta_evidence)
        self.assertIn("stability_strength", stat.stat_evidence)
        self.assertIn("edge_selection_frequency", gdn.gdn_evidence)
        self.assertNotIn("merged_score", self.result.cohort.to_dict())

    def test_identity_list_hash_is_deterministic(self) -> None:
        expected = stable_hash_v1({"artifact_type": "candidate_profiling_identity_list_v1", "identities": [{"source": a, "target": b} for a, b in self.result.cohort.candidate_identity_list]})
        self.assertEqual(self.result.cohort.candidate_identity_list_hash, expected)

    def test_build_is_deterministic(self) -> None:
        again = build_task039c_integration_v1(**self.inputs, integration_execution_code_commit=EXECUTION_PLACEHOLDER)
        self.assertEqual(self.result.cohort.to_dict(), again.cohort.to_dict())
        self.assertEqual(self.result.receipt.to_dict(), again.receipt.to_dict())

    def test_all_contracts_round_trip(self) -> None:
        self.assertEqual(TASK039CThreeArmOverlapV1.from_dict(self.result.overlap.to_dict()).artifact_hash, self.result.overlap.artifact_hash)
        self.assertEqual(CandidateProfilingCohortV1.from_dict(self.result.cohort.to_dict()).artifact_hash, self.result.cohort.artifact_hash)
        self.assertEqual(TASK039D0AuthorizationV1.from_dict(self.result.authorization.to_dict()).artifact_hash, self.result.authorization.artifact_hash)
        self.assertEqual(TASK039CIntegrationReceiptV1.from_dict(self.result.receipt.to_dict()).artifact_hash, self.result.receipt.artifact_hash)

    def test_unknown_fields_rejected(self) -> None:
        for contract, document in (
            (TASK039CArmBindingV1, self.result.cohort.arm_bindings[0].to_dict()),
            (CandidateProfilingEntryV1, self.result.cohort.candidates[0].to_dict()),
            (TASK039CThreeArmOverlapV1, self.result.overlap.to_dict()),
            (CandidateProfilingCohortV1, self.result.cohort.to_dict()),
            (TASK039D0AuthorizationV1, self.result.authorization.to_dict()),
            (TASK039CIntegrationReceiptV1, self.result.receipt.to_dict()),
        ):
            broken = copy.deepcopy(document)
            broken["unexpected"] = True
            with self.subTest(contract=contract.__name__), self.assertRaises(CandidateIntegrationError):
                contract.from_dict(broken)

    def test_self_hash_mutation_rejected(self) -> None:
        broken = self.result.cohort.to_dict()
        broken["union_count"] = 46
        with self.assertRaises(CandidateIntegrationError):
            CandidateProfilingCohortV1.from_dict(broken)

    def test_absolute_path_and_private_content_rejected(self) -> None:
        with self.assertRaises(CandidateIntegrationError):
            assert_public_payload_v1({"path": "C:\\private\\data.csv"})
        with self.assertRaises(CandidateIntegrationError):
            assert_public_payload_v1({"private_ledger_contents": []})

    def test_task039d0_is_design_only(self) -> None:
        authorization = self.result.authorization
        self.assertTrue(authorization.protocol_design_authorized)
        self.assertFalse(authorization.real_hai_profiling_authorized)
        self.assertFalse(authorization.train1_train2_profiling_execution_authorized)
        self.assertFalse(authorization.rule_v2_authorized)

    def test_no_hai_private_br2_or_profiling_access(self) -> None:
        cohort = self.result.cohort
        receipt = self.result.receipt
        self.assertFalse(cohort.hai_feature_values_accessed_by_integration)
        self.assertFalse(cohort.private_ledgers_accessed_by_integration)
        self.assertFalse(cohort.br2_relation_outcomes_used)
        self.assertFalse(cohort.relation_profiling_executed)
        self.assertFalse(receipt.hai_feature_access or receipt.private_ledger_access or receipt.br2_ground_truth_used)

    def test_new_schemas_are_draft_2020_12_and_closed(self) -> None:
        names = (
            "task039c_arm_binding_v1_schema.json", "task039c_three_arm_overlap_v1_schema.json",
            "candidate_profiling_entry_v1_schema.json", "candidate_profiling_cohort_v1_schema.json",
            "task039c_integration_receipt_v1_schema.json", "task039d0_authorization_v1_schema.json",
        )
        for name in names:
            schema = json.loads((ROOT / "schemas" / "v6" / name).read_text(encoding="utf-8"))
            with self.subTest(name=name):
                Draft202012Validator.check_schema(schema)
                self.assertFalse(schema["additionalProperties"])

    def test_registry_contains_merged_and_integration_artifacts(self) -> None:
        types = set(load_v6_schema_registry_v1(repository_root=ROOT).artifact_types)
        self.assertTrue({"metadata_candidate_result_v1", "statistical_candidate_result_v1", "gdn_candidate_result_v1", "task039c_gdn_final_audit_v1", "candidate_profiling_cohort_v1", "task039d0_authorization_v1"} <= types)


if __name__ == "__main__":
    unittest.main()
