from __future__ import annotations
from dataclasses import replace
import unittest

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d2_execution_authorization_v1 import *


class IndependentD2AuthorizationAttacks(unittest.TestCase):
    def test_all_rehashed_semantic_attacks_reject(self):
        receipt=build_synthetic_d2_execution_custody_preflight_receipt_v1()
        auth=issue_d2_inner_execution_authorization_v1(receipt)
        attacks=[
            ('d2_design_hash','0'*64),('provenance_clarification_hash','1'*64),
            ('d0_prediction_hash','2'*64),('d1_prediction_hash','3'*64),
            ('source_map_hash','4'*64),('required_distinct_source_count',1),
            ('required_distinct_source_count',3),('same_second_policy','WINDOWED'),
            ('d0_preservation_policy','SUPPRESS_D0'),('d0_rerun_authorized',True),
            ('d1_rerun_authorized',True),('d0_score_access_authorized',True),
            ('rule_reevaluation_authorized',True),('fusion_change_authorized',True),
            ('fusion_candidate_search_authorized',True),
            ('label_access_before_combined_prediction_freeze_authorized',True),
            ('test1_feature_access_authorized',True),('test2_authorized',True),
            ('outer_authorized',True),('future_record_count',53999),
            ('future_artifact_family','AlternatePrediction'),
            ('allowed_trigger_classes',('NONE','RAW_RULE_OR')),
            ('primary_metric_formulas',('MUTATED',)),
            ('incremental_metric_formulas',('RESULT_DEPENDENT_SELECTION',)),
            ('future_execution_order',('LABEL_FIRST','FUSE')),
        ]
        accepted=0
        for field,value in attacks:
            forged=replace(auth,**{field:value})
            payload=forged._payload()
            forged=replace(forged,authorization_hash=stable_hash_v1(payload))
            try: validate_d2_inner_execution_authorization_v1(forged,receipt)
            except D2ExecutionAuthorizationError: continue
            accepted+=1
        self.assertEqual(len(attacks),25)
        self.assertEqual(accepted,0)

    def test_source_map_substitution_and_cardinality_attacks_reject(self):
        source=build_d2_source_resolution_map_v1()
        attacks=(
            replace(source,entry_count=41),replace(source,entry_count=43),
            replace(source,unique_relation_count=41),replace(source,distinct_source_count=8),
            replace(source,entries=source.entries[:-1]),
            replace(source,entries=source.entries+(source.entries[0],)),
            replace(source,entries=(replace(source.entries[0],source_variable_identity='SUBSTITUTED'),)+source.entries[1:]),
        )
        accepted=0
        for forged in attacks:
            forged=replace(forged,source_map_hash=stable_hash_v1(forged._payload()))
            try: validate_d2_source_resolution_map_v1(forged)
            except D2ExecutionAuthorizationError: continue
            accepted+=1
        self.assertEqual(accepted,0)


if __name__=='__main__': unittest.main()
