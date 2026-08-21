from __future__ import annotations
import copy
from dataclasses import replace
import inspect
import unittest

from paperworks.v6.task039e3_r2r_d2_execution_authorization_v1 import *


class D2ExecutionAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.receipt=build_synthetic_d2_execution_custody_preflight_receipt_v1()

    def test_exact_public_replay_and_source_map(self):
        replay=replay_required_d2_public_authorities_v1()
        self.assertTrue(replay.authority_set_hash)
        source=self.receipt._source_map
        self.assertEqual(validate_d2_source_resolution_map_v1(source),source.source_map_hash)
        self.assertEqual((source.entry_count,source.unique_relation_count,source.distinct_source_count),(42,42,9))

    def test_synthetic_authorization_is_exact_and_nonreal(self):
        auth=issue_d2_inner_execution_authorization_v1(self.receipt)
        self.assertEqual(validate_d2_inner_execution_authorization_v1(auth,self.receipt),auth.authorization_hash)
        self.assertFalse(auth.d2_inner_execution_authorized)
        self.assertFalse(auth.label_access_before_combined_prediction_freeze_authorized)
        self.assertFalse(auth.test1_feature_access_authorized)
        self.assertFalse(auth.test2_authorized)

    def test_reconstruction_copy_replace_and_self_rehash_reject(self):
        source=self.receipt._source_map
        for forged in (copy.deepcopy(source),replace(source),replace(source,source_map_hash='0'*64)):
            with self.assertRaises(D2ExecutionAuthorizationError): validate_d2_source_resolution_map_v1(forged)
        auth=issue_d2_inner_execution_authorization_v1(self.receipt)
        for forged in (copy.deepcopy(auth),replace(auth),replace(auth,authorization_hash='1'*64)):
            with self.assertRaises(D2ExecutionAuthorizationError): validate_d2_inner_execution_authorization_v1(forged,self.receipt)

    def test_no_caller_scientific_knobs(self):
        self.assertEqual(tuple(inspect.signature(build_synthetic_d2_execution_custody_preflight_receipt_v1).parameters),())
        self.assertEqual(tuple(inspect.signature(perform_d2_inner_execution_custody_preflight_v1).parameters),())

    def test_all_authorization_escalations_false(self):
        auth=issue_d2_inner_execution_authorization_v1(self.receipt)
        fields=('label_access_before_combined_prediction_freeze_authorized','test1_feature_access_authorized','d0_rerun_authorized','d1_rerun_authorized','d0_score_access_authorized','rule_reevaluation_authorized','fusion_change_authorized','fusion_candidate_search_authorized','test2_authorized','outer_authorized')
        self.assertTrue(all(getattr(auth,name) is False for name in fields))


if __name__=='__main__': unittest.main()
