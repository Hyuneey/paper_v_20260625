import unittest
from dataclasses import replace
import numpy as np

from paperworks.validation_v2.xver_detector_v1 import (
    ExternalNormalMatrixV1, ExternalDetectorError, fit_external_pca_v1,
    score_external_pca_v1, calibrate_external_v1,
)
from paperworks.validation_v2.multipanel_metrics_v1 import *
from paperworks.validation_v2.multipanel_custody_v1 import *
from paperworks.validation_v2.p1_eligibility_custodian_v1 import *

H='a'*64; C='b'*40


class DetectorPortabilityTests(unittest.TestCase):
    def matrix(self, split, columns=3):
        rng=np.random.default_rng(123 if split=='train1' else 456)
        return ExternalNormalMatrixV1('22.04',split,H,tuple(f'P1_X{i}' for i in range(columns)),rng.normal(size=(300,columns)))
    def test_pca_is_dimension_agnostic_and_split_pure(self):
        first,second=self.matrix('train1'),self.matrix('train2')
        model=fit_external_pca_v1(first,second,version='22.04',feature_ids=first.feature_ids,source_commit=C,preregistration_hash=H)
        scores,binding=score_external_pca_v1(model,second,split='train2')
        threshold=calibrate_external_v1(scores,binding,fit_hash=model.fit_authority['self_hash'],config_hash=model.fit_authority['method_config_hash'])
        self.assertEqual(threshold['score_count'],300)
        self.assertEqual(model.fit_authority['residual_dimension_count']+model.fit_authority['component_count'],3)
        with self.assertRaises(ExternalDetectorError):
            fit_external_pca_v1(first,replace(second,split_id='train3'),version='22.04',feature_ids=first.feature_ids,source_commit=C,preregistration_hash=H)
    def test_non_p1_and_nonfinite_fail(self):
        bad=replace(self.matrix('train1'),feature_ids=('BAD','P1_X1','P1_X2'))
        with self.assertRaises(ExternalDetectorError):
            fit_external_pca_v1(bad,self.matrix('train2'),version='22.04',feature_ids=bad.feature_ids,source_commit=C,preregistration_hash=H)


class MetricTests(unittest.TestCase):
    def test_empty_and_wilson(self):
        self.assertEqual(scenario_recall_v1([])['status'],'NOT_EVALUABLE')
        self.assertEqual(scenario_recall_v1([False,False])['recall'],0)
        self.assertIsNone(wilson95_v1(0,0));self.assertEqual(wilson95_v1(1,1)[1],1)
    def test_file_boundaries_and_zero_alarm(self):
        result=false_burden_v1({'b':[True],'a':[True,True]},{'a':2,'b':1})
        self.assertEqual(result['false_episodes'],2)
        zero=false_burden_v1({'a':[False,False]},{'a':2})
        self.assertEqual((zero['false_episodes_per_hour'],zero['false_seconds_per_hour']),(0,0))
    def test_delay_pairing_and_mcnemar(self):
        self.assertEqual(detection_delay_v1(10,[8,12],20),2)
        self.assertIsNone(detection_delay_v1(10,[8,21],20))
        table=paired_scenario_table_v1([True,False],[False,True])
        self.assertEqual((table['a_only'],table['b_only']),(1,1))
        self.assertEqual(mcnemar_exact_v1(0,0)['status'],'NOT_APPLICABLE_NO_DISCORDANCE')


class CustodyEligibilityTests(unittest.TestCase):
    def cell(self,panel,file,method):
        return PredictionCellReceiptV1(panel,file,method,H,H,H,2,H,0,0,1,C)
    def test_global_cell_census_and_one_shot_lease(self):
        cells=(('P1','F1','M0'),('P2','F2','M0')); receipts=tuple(self.cell(*x) for x in cells)
        manifest=GlobalPredictionManifestV1(cells,receipts,H,H,H);manifest.validate()
        lease=issue_label_scenario_lease_v1(manifest)
        self.assertEqual(consume_label_scenario_lease_v1(lease,manifest,lambda:'labels'),'labels')
        with self.assertRaises(MultiPanelCustodyError):consume_label_scenario_lease_v1(lease,manifest,lambda:None)
        with self.assertRaises(MultiPanelCustodyError):GlobalPredictionManifestV1(cells,receipts[:1],H,H,H).validate()
        for before,after in zip(tuple(GlobalPredictionStateV1),tuple(GlobalPredictionStateV1)[1:]):validate_state_transition_v1(before,after)
        with self.assertRaises(MultiPanelCustodyError):
            validate_state_transition_v1(GlobalPredictionStateV1.ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED,GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED)
        failed=replace(receipts[0],terminal_status='METHOD_FAILURE')
        GlobalPredictionManifestV1(cells,(failed,receipts[1]),H,H,H).validate()
    def test_feature_projection_and_postfreeze_mutation(self):
        value={'panel_id':'P','file_id':'F','timestamp_id':'t','approved_feature_ids':['P1_X'],'projection_hash':H,'row_count':2,'label_values_parsed':False,'scenario_values_parsed':False}
        validate_attack_feature_projection_contract_v1(value)
        with self.assertRaises(MultiPanelCustodyError):validate_attack_feature_projection_contract_v1({**value,'label_values_parsed':True})
        def forbidden(): raise AssertionError('excluded value parsed')
        readers={'time':lambda:[1,2],'P1_X':lambda:[3.,4.],'attack':forbidden,'scenario':forbidden}
        first=project_attack_columns_v1(header=tuple(readers),column_readers=readers,timestamp_id='time',approved_feature_ids=('P1_X',))
        readers['attack']=lambda:['malformed','different']
        second=project_attack_columns_v1(header=tuple(readers),column_readers=readers,timestamp_id='time',approved_feature_ids=('P1_X',))
        self.assertEqual(first,second);self.assertNotIn('attack',first);self.assertNotIn('scenario',first)
    def test_method_blind_p1_logic(self):
        mapping={'P1_X':'P1','P2_X':'OUT_OF_SCOPE','MYSTERY':'UNRESOLVED'}
        self.assertEqual(classify_p1_scenario_v1(OfficialScenarioMetadataV1('v','f','s',('P1_X',)),mapping,mapping_authority_hash=H)['status'],'P1_ELIGIBLE')
        self.assertEqual(classify_p1_scenario_v1(OfficialScenarioMetadataV1('v','f','s',('P2_X',),('P1',)),mapping,mapping_authority_hash=H)['status'],'CROSS_PROCESS_P1_RELEVANT')
        self.assertEqual(classify_p1_scenario_v1(OfficialScenarioMetadataV1('v','f','s',('MYSTERY',)),mapping,mapping_authority_hash=H)['status'],'UNRESOLVED')
        with self.assertRaises(ValueError):assert_method_blind_payload_v1({'detector_score':1})


if __name__=='__main__':unittest.main()
