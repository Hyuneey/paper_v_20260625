import unittest
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
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

    def test_hai23_private_detector_authority_is_exactly_hash_bound(self):
        root=Path(__file__).resolve().parents[1]/'research_control_center/validation_v2/multipanel_pre_dg05'
        binding=json.loads((root/'HAI23_DETECTOR_PRIVATE_HASH_BINDING_V1.json').read_text(encoding='utf-8'))
        replay=json.loads((root/'HAI23_DETECTOR_REPLAY_AUTHORITY_V1.json').read_text(encoding='utf-8'))
        self.assertEqual(binding['status'],'EXACT_PRIVATE_HASH_REPLAY_PASS')
        self.assertEqual(replay['private_model_bytes'],'EXACT_HASH_BOUND_LOCAL_ONLY')
        self.assertEqual(replay['private_hash_binding'],binding['self_hash'])
        for key in ('pca_fit_authority_hash','pca_threshold_authority_hash','if_fit_authority_hash','if_threshold_authority_hash'):
            self.assertEqual(replay[key],binding[key])
        self.assertFalse(binding['private_paths_published'])
        self.assertFalse(binding['private_numeric_values_published'])
        self.assertFalse(binding['model_bytes_deserialized'])
        self.assertEqual(binding['test_or_attack_payload_accesses'],0)
        self.assertEqual(binding['label_or_scenario_accesses'],0)


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
    def test_official_scenario_overlap_and_exact_pair_alignment(self):
        scenarios=(EligibleScenarioIntervalV1('23.05','f1','s2',10,20,H,H),EligibleScenarioIntervalV1('23.05','f1','s1',1,5,H,H))
        a=official_scenario_recall_v1(scenarios,{('23.05','f1'):(4,21)})
        b_hits=official_scenario_hits_v1(scenarios,{('23.05','f1'):(15,)})
        self.assertEqual((a['hits'],a['eligible'],a['recall']),(1,2,.5))
        table=paired_official_scenario_table_v1(tuple(ScenarioHitV1(x['dataset_version'],x['file_id'],x['scenario_id'],x['hit'],x['scenario_authority_hash'],x['eligibility_authority_hash']) for x in a['scenario_hits']),b_hits)
        self.assertEqual((table['a_only'],table['b_only'],table['aligned_scenario_count']),(1,1,2))
        with self.assertRaises(MultiPanelMetricError):
            paired_official_scenario_table_v1(b_hits,(ScenarioHitV1('23.05','f1','different',True,H,H),))
        with self.assertRaises(MultiPanelMetricError):
            official_scenario_recall_v1((EligibleScenarioIntervalV1('23.05','f1','s',0,1,H,H),EligibleScenarioIntervalV1('22.04','f2','s',0,1,H,H)),{('23.05','f1'):(),('22.04','f2'):()})
        with self.assertRaises(MultiPanelMetricError):
            paired_official_scenario_table_v1(b_hits,tuple(replace(row,eligibility_authority_hash='b'*64) for row in b_hits))
        with self.assertRaises(MultiPanelMetricError):
            assert_single_version_records_v1((scenarios[0],EligibleScenarioIntervalV1('22.04','f2','s',0,1,H,H)))
        self.assertEqual(paired_scenario_table_v1([],[])['status'],'NOT_EVALUABLE')
    def test_delay_inputs_fail_closed(self):
        for alarms in ((1.5,), (True,), (-1,)):
            with self.assertRaises(MultiPanelMetricError):detection_delay_v1(0,alarms,10)
        for delays in ((True,),(-1,),('1',)):
            with self.assertRaises(MultiPanelMetricError):summarize_delays_v1(delays)


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

    def allowlists_v2(self):
        return {panel:FrozenFeatureAllowlistAuthorityV2(panel,'23.05' if 'HAI23' in panel else ('22.04' if 'HAI22' in panel else '21.03'),'time',('P1_X',),H,C)
                for panel in FROZEN_PANEL_ORDER_V2}

    def census_v2(self):
        methods=[]
        for panel in FROZEN_PANEL_ORDER_V2:
            ids=PRIMARY_METHODS_V2+SECONDARY_METHODS_V2[panel]
            methods.append((panel,tuple(MethodCellAuthorityV2(item,H,H) for item in ids)))
        return GlobalCellCensusAuthorityV2(tuple((panel,(f'f{index}',)) for index,panel in enumerate(FROZEN_PANEL_ORDER_V2)),tuple(methods),H,H,C)

    def manifest_v2(self,root:Path):
        census=self.census_v2();allowlists=self.allowlists_v2();projections=[];artifacts={}
        for index,(panel,files) in enumerate(census.files_by_panel):
            file_id=files[0];authority=allowlists[panel]
            values,projection=project_attack_columns_v2(header=('time','P1_X','label'),column_readers={'time':lambda:[1,2], 'P1_X':lambda:[3.,4.], 'label':lambda:(_ for _ in ()).throw(AssertionError('excluded read'))},authority=authority,file_id=file_id,raw_container_hash=H,source_commit=C)
            self.assertEqual(set(values),{'time','P1_X'});projections.append(projection)
            for method in dict(census.methods_by_panel)[panel]:
                cell=(panel,file_id,method.method_id);payload=json.dumps({'cell':cell}).encode();path=root/f'artifact-{index}-{method.method_id}.json';path.write_bytes(payload);artifacts[cell]=path
        fixed=[]
        for cell,path in artifacts.items():
            panel,file_id,method_id=cell;projection=next(p for p in projections if p.panel_id==panel and p.file_id==file_id)
            fixed.append(PredictionSuccessReceiptV2(panel,file_id,method_id,H,H,projection.projection_hash,sha256(path.read_bytes()).hexdigest(),2,projection.timestamp_range_hash,0,1,C))
        manifest=GlobalPredictionManifestV2(census,tuple(projections),tuple(fixed),H,H,H,H,C)
        return manifest,allowlists,artifacts

    def test_v2_durable_global_freeze_and_one_shot_lease(self):
        with TemporaryDirectory() as raw:
            root=Path(raw);manifest,allowlists,artifacts=self.manifest_v2(root)
            freeze=persist_global_manifest_v2(root,manifest,allowlists,artifacts)
            transition=initialize_state_chain_v2(root,census_authority_hash=manifest.census.document()['self_hash'],evaluation_policy_hash=H,metric_authority_hash=H,p1_custodian_authority_hash=H,dg05_authorization_hash=H,source_commit=C)
            for state in tuple(GlobalPredictionStateV1)[1:4]:transition=advance_state_chain_v2(root,transition,state)
            lease=issue_label_scenario_lease_v2(root,manifest,freeze,transition,allowlists)
            self.assertEqual(consume_label_scenario_lease_v2(lease,manifest,allowlists,lambda:'labels'),'labels')
            with self.assertRaises(MultiPanelCustodyError):consume_label_scenario_lease_v2(lease,manifest,allowlists,lambda:None)
            with self.assertRaises(MultiPanelCustodyError):issue_label_scenario_lease_v2(root,manifest,freeze,transition,allowlists)
            with self.assertRaises(MultiPanelCustodyError):LabelScenarioLeaseV2(None,'x',H,H,root)

    def test_v2_failure_receipt_has_no_prediction_fields(self):
        census=self.census_v2();panel,file_id,method_id=census.expected_cells()[0]
        failure=PredictionFailureReceiptV2(panel,file_id,method_id,H,H,H,2,H,'SYSTEM_ERROR',H,1,1,C)
        failure.validate(census);document=failure.document()
        self.assertNotIn('prediction_artifact_hash',document);self.assertNotIn('alarm_count',document)
        with self.assertRaises(MultiPanelCustodyError):replace(failure,system_error_count=0).validate(census)

    def test_v2_projection_is_authority_bound_and_label_invariant(self):
        authority=self.allowlists_v2()[FROZEN_PANEL_ORDER_V2[0]]
        def project(label):
            readers={'time':lambda:[1,2],'P1_X':lambda:[3.,4.],'label':lambda:label}
            return project_attack_columns_v2(header=tuple(readers),column_readers=readers,authority=authority,file_id='f',raw_container_hash=H,source_commit=C)
        first=project([0,0]);second=project(['bad',object()])
        self.assertEqual(first[0],second[0]);self.assertEqual(first[1].projection_hash,second[1].projection_hash)
        with self.assertRaises(MultiPanelCustodyError):
            project_attack_columns_v2(header=('time','P1_X'),column_readers={'time':lambda:[1],'P1_X':lambda:[2]},authority=replace(authority,feature_ids=('P1_X','P1_UNKNOWN')),file_id='f',raw_container_hash=H,source_commit=C)

    def test_v2_p1_mapping_authority_and_nested_taint(self):
        authority=FrozenP1MappingAuthorityV2('22.04',(P1MappingEntryV2('P1_X','P1','EXACT_MATCH',H),P1MappingEntryV2('P2_X','OUT_OF_SCOPE','EXACT_MATCH',H)),H,C)
        scenario=OfficialScenarioMetadataV2('22.04','f','s',('P1_X',),(),H,H)
        result=classify_p1_scenario_v2(scenario,authority)
        self.assertEqual(result['status'],'P1_ELIGIBLE');self.assertEqual(result['mapping_authority_hash'],authority.document()['self_hash'])
        with self.assertRaises(ValueError):classify_p1_scenario_v2(replace(scenario,dataset_version='21.03'),authority)
        with self.assertRaises(ValueError):assert_method_blind_nested_v2({'nested':{'detector_score':1}})
        with self.assertRaises(ValueError):replace(authority,entries=(P1MappingEntryV2('P1_X','P1','UNRESOLVED',H),)).validate()


if __name__=='__main__':unittest.main()
