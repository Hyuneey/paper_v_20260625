from __future__ import annotations

import unittest

from paperworks.profiling.task039d1_final_audit_v1 import (
    CONFIRMATION_POLICY_HASH,
    DIRECTIONAL_LEDGER_HASH,
    FIT_RESULT_HASH,
    PAIR_SUMMARY_HASH,
    READINESS,
    SOURCE_LEDGER_HASH,
    TARGET_LEDGER_HASH,
    TASK039D2AuthorizationV1,
    build_d2_authorization_v1,
    verify_audit_self_hash_v1,
)


class TASK039D2AuthorizationTests(unittest.TestCase):
    def test_authorization_is_one_way_and_requires_clean_execution_commit(self) -> None:
        document = build_d2_authorization_v1()
        verify_audit_self_hash_v1(document)
        TASK039D2AuthorizationV1.from_dict(document)
        self.assertEqual(document["readiness"], READINESS)
        self.assertEqual(document["confirmation_policy_hash"], CONFIRMATION_POLICY_HASH)
        self.assertEqual(document["d1_fit_result_hash"], FIT_RESULT_HASH)
        self.assertEqual(document["d1_source_ledger_hash"], SOURCE_LEDGER_HASH)
        self.assertEqual(document["d1_target_ledger_hash"], TARGET_LEDGER_HASH)
        self.assertEqual(document["d1_directional_ledger_hash"], DIRECTIONAL_LEDGER_HASH)
        self.assertEqual(document["d1_pair_summary_hash"], PAIR_SUMMARY_HASH)
        self.assertEqual(document["input_directional_relation_count"], 45)
        self.assertEqual(document["supported_pair_context_count"], 25)
        self.assertTrue(document["train3_feature_values_authorized"])
        self.assertTrue(document["separate_clean_d2_execution_code_commit_required"])
        for field in (
            "train1_train2_feature_value_refitting_authorized",
            "train4_authorized",
            "test_labels_attacks_authorized",
            "br2_pair_results_authorized",
            "candidate_arm_evidence_visible_to_confirmation_engine",
            "parameter_retuning_authorized",
            "alternative_horizon_search_authorized",
            "opposite_target_direction_search_authorized",
            "rule_v2_authorized",
            "agent_authorized",
            "detector_runtime_authorized",
            "d2_executed_by_this_artifact",
        ):
            self.assertFalse(document[field])


if __name__ == "__main__":
    unittest.main()
