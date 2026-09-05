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
BUNDLE='dab320da47489e5093862b7c4675523c3e6b710faceb753e7f39c8e56f002fe2'


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
        return {panel:FrozenFeatureAllowlistAuthorityV2(panel,FROZEN_DATASET_VERSIONS_V2[panel],FROZEN_TIMESTAMP_IDS_V2[panel],FROZEN_FEATURE_IDS_V2[panel],BUNDLE,C)
                for panel in FROZEN_PANEL_ORDER_V2}

    def physical_v2(self):
        files=[]
        for panel in FROZEN_PANEL_ORDER_V2:
            header=[FROZEN_TIMESTAMP_IDS_V2[panel],*FROZEN_FEATURE_IDS_V2[panel],'label']
            header_hash=sha256(json.dumps({'header':header},sort_keys=True,separators=(',',':')).encode()).hexdigest()
            files.extend(PhysicalFileIdentityV2(panel,file_id,H,header_hash,H) for file_id in FROZEN_ATTACK_FILE_IDS_V2[panel])
        return FrozenPhysicalFileAuthorityV2(tuple(files),FROZEN_ATTACK_FILE_CENSUS_HASH_V2,H,C)

    def census_v2(self,allowlists=None,physical=None):
        allowlists=allowlists or self.allowlists_v2();physical=physical or self.physical_v2()
        methods=[(panel,frozen_method_cell_authorities_v2(panel)) for panel in FROZEN_PANEL_ORDER_V2]
        allowlist_hashes=tuple((panel,allowlists[panel].document()['self_hash']) for panel in FROZEN_PANEL_ORDER_V2)
        return GlobalCellCensusAuthorityV2(tuple((panel,FROZEN_ATTACK_FILE_IDS_V2[panel]) for panel in FROZEN_PANEL_ORDER_V2),tuple(methods),BUNDLE,physical.document()['self_hash'],allowlist_hashes,C)

    def manifest_v2(self,root:Path):
        allowlists=self.allowlists_v2();physical=self.physical_v2();census=self.census_v2(allowlists,physical)
        projections=[];projection_artifacts={};artifacts={}
        index=0
        for panel,files in census.files_by_panel:
            authority=allowlists[panel];selected=(authority.timestamp_id,*authority.feature_ids)
            for file_id in files:
                readers={name:(lambda:[1,2]) if name==authority.timestamp_id else (lambda:[3.,4.]) for name in selected}
                readers['label']=lambda:(_ for _ in ()).throw(AssertionError('excluded read'))
                values,projection=project_attack_columns_v2(header=tuple(readers),column_readers=readers,authority=authority,file_id=file_id,raw_container_hash=H,source_commit=C)
                self.assertEqual(set(values),set(selected));projections.append(projection)
                projection_path=root/f'projection-{index}.json';projection_path.write_bytes(canonical_projection_bytes_v2(values,selected))
                projection_artifacts[(panel,file_id)]=projection_path
                for method in dict(census.methods_by_panel)[panel]:
                    cell=(panel,file_id,method.method_id);artifacts[cell]=root/f'artifact-{index}-{method.method_id}.json'
                index+=1
        fixed=[]
        for cell,path in artifacts.items():
            panel,file_id,method_id=cell;projection=next(p for p in projections if p.panel_id==panel and p.file_id==file_id)
            method=census.method(panel,method_id)
            provisional=PredictionSuccessReceiptV2(panel,file_id,method_id,method.method_authority_hash,method.execution_authority_hash,projection.projection_hash,H,2,projection.timestamp_range_hash,0,1,C)
            payload=build_prediction_artifact_v2(provisional,(False,False));path.write_bytes(payload)
            fixed.append(replace(provisional,prediction_artifact_hash=sha256(payload).hexdigest()))
        manifest=GlobalPredictionManifestV2(census,tuple(projections),tuple(fixed),H,H,H,H,C)
        return manifest,allowlists,physical,projection_artifacts,artifacts

    def issued_v2(self,root:Path):
        manifest,allowlists,physical,projections,artifacts=self.manifest_v2(root)
        freeze=persist_global_manifest_v2(root,manifest,allowlists,physical,projections,artifacts)
        transition=initialize_state_chain_v2(root,census_authority_hash=manifest.census.document()['self_hash'],evaluation_policy_hash=H,metric_authority_hash=H,p1_custodian_authority_hash=H,dg05_authorization_hash=H,source_commit=C)
        def evidence(name,schema,**extra):
            body={'schema':schema,**extra};body['self_hash']=sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            path=root/name;path.write_bytes(json.dumps(body,sort_keys=True,separators=(',',':')).encode()+b'\n');return path,body
        path,item=evidence('feature-projection-census.freeze.json','multipanel_feature_projection_census_freeze_v2',census_authority_hash=manifest.census.document()['self_hash'])
        transition=advance_state_chain_v2(root,transition,GlobalPredictionStateV1.ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED,evidence_kind='FEATURE_PROJECTION_CENSUS_FREEZE',evidence_hash=item['self_hash'],evidence_path=path)
        path,item=evidence('prediction-execution-start.json','multipanel_prediction_execution_start_receipt_v2',projection_transition_hash=transition['self_hash'])
        transition=advance_state_chain_v2(root,transition,GlobalPredictionStateV1.PREDICTIONS_IN_PROGRESS_LABEL_LOCKED,evidence_kind='PREDICTION_EXECUTION_START_RECEIPT',evidence_hash=item['self_hash'],evidence_path=path)
        transition=advance_state_chain_v2(root,transition,GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED,evidence_kind='GLOBAL_MANIFEST_FREEZE',evidence_hash=freeze['self_hash'],evidence_path=root/'global_prediction_manifest_v2.freeze.json')
        lease=issue_label_scenario_lease_v2(root,manifest,freeze,transition,allowlists,physical,projections,artifacts)
        return manifest,allowlists,physical,projections,artifacts,freeze,transition,lease

    def test_v2_durable_global_freeze_and_one_shot_lease(self):
        with TemporaryDirectory() as raw:
            root=Path(raw);manifest,allowlists,physical,projections,artifacts,freeze,transition,lease=self.issued_v2(root)
            self.assertEqual(consume_label_scenario_lease_v2(lease,manifest,allowlists,physical,projections,artifacts,lambda:'labels'),'labels')
            completion=json.loads((root/'label-scenario-lease.completed.json').read_text(encoding='utf-8'))
            result_receipt={'schema':'multipanel_result_integrity_receipt_v2','lease_completion_receipt_hash':completion['self_hash'],
                            'lease_open_transition_hash':lease.lease_open_transition_hash,'result_bundle_hash':H}
            final=complete_results_state_v2(root,lease,result_receipt)
            self.assertEqual(final['state'],GlobalPredictionStateV1.RESULTS_COMPUTED.value)
            with self.assertRaises(MultiPanelCustodyError):consume_label_scenario_lease_v2(lease,manifest,allowlists,physical,projections,artifacts,lambda:None)
            with self.assertRaises(MultiPanelCustodyError):issue_label_scenario_lease_v2(root,manifest,freeze,transition,allowlists,physical,projections,artifacts)
            with self.assertRaises(MultiPanelCustodyError):LabelScenarioLeaseV2(None,'x',H,H,H,root)

    def test_v2_post_issue_artifact_and_manifest_mutation_block_reader(self):
        for mutate in ('prediction','projection','manifest'):
            with self.subTest(mutate=mutate),TemporaryDirectory() as raw:
                root=Path(raw);manifest,allowlists,physical,projections,artifacts,_,_,lease=self.issued_v2(root)
                target=(next(iter(artifacts.values())) if mutate=='prediction' else
                        next(iter(projections.values())) if mutate=='projection' else root/'global_prediction_manifest_v2.json')
                target.write_bytes(target.read_bytes()+b' ')
                called=[]
                with self.assertRaises(MultiPanelCustodyError):
                    consume_label_scenario_lease_v2(lease,manifest,allowlists,physical,projections,artifacts,lambda:called.append(True))
                self.assertEqual(called,[])

    def test_v2_tampered_issue_receipt_blocks_reader(self):
        with TemporaryDirectory() as raw:
            root=Path(raw);manifest,allowlists,physical,projections,artifacts,_,_,lease=self.issued_v2(root)
            path=root/'label-scenario-lease.issue.json';value=json.loads(path.read_text(encoding='utf-8'))
            value['manifest_hash']='f'*64;path.write_text(json.dumps(value),encoding='utf-8')
            called=[]
            with self.assertRaises(MultiPanelCustodyError):
                consume_label_scenario_lease_v2(lease,manifest,allowlists,physical,projections,artifacts,lambda:called.append(True))
            self.assertEqual(called,[])

    def test_v2_reader_failure_is_durably_consumed(self):
        with TemporaryDirectory() as raw:
            root=Path(raw);manifest,allowlists,physical,projections,artifacts,_,_,lease=self.issued_v2(root)
            def fail():raise RuntimeError('synthetic reader failure')
            with self.assertRaisesRegex(MultiPanelCustodyError,'LABEL_READER_FAILED_LEASE_CONSUMED'):
                consume_label_scenario_lease_v2(lease,manifest,allowlists,physical,projections,artifacts,fail)
            completion=json.loads((root/'label-scenario-lease.completed.json').read_text(encoding='utf-8'))
            self.assertEqual(completion['reader_status'],'READER_FAILED_LEASE_CONSUMED')
            with self.assertRaises(MultiPanelCustodyError):
                consume_label_scenario_lease_v2(lease,manifest,allowlists,physical,projections,artifacts,lambda:None)

    def test_v2_reader_cannot_mutate_frozen_prediction_artifact(self):
        with TemporaryDirectory() as raw:
            root=Path(raw);manifest,allowlists,physical,projections,artifacts,_,_,lease=self.issued_v2(root)
            target=next(iter(artifacts.values()))
            def mutate():target.write_bytes(target.read_bytes()+b' ');return 'labels'
            with self.assertRaisesRegex(MultiPanelCustodyError,'POST_READ_FROZEN_ARTIFACT_MUTATION'):
                consume_label_scenario_lease_v2(lease,manifest,allowlists,physical,projections,artifacts,mutate)
            completion=json.loads((root/'label-scenario-lease.completed.json').read_text(encoding='utf-8'))
            self.assertEqual(completion['reader_status'],'POST_READ_FROZEN_ARTIFACT_MUTATION')

    def test_v2_authority_cross_binding_and_transition_prerequisites(self):
        allowlists=self.allowlists_v2();physical=self.physical_v2();census=self.census_v2(allowlists,physical)
        with self.assertRaises(MultiPanelCustodyError):
            replace(census,method_bundle_hash=H).validate()
        bad_allowlists=dict(allowlists);panel=FROZEN_PANEL_ORDER_V2[0]
        bad_allowlists[panel]=replace(bad_allowlists[panel],source_commit='c'*40)
        with TemporaryDirectory() as raw:
            root=Path(raw);manifest,_,physical,projections,artifacts=self.manifest_v2(root)
            with self.assertRaises(MultiPanelCustodyError):manifest.validate(bad_allowlists,physical)
            current=initialize_state_chain_v2(root,census_authority_hash=manifest.census.document()['self_hash'],evaluation_policy_hash=H,metric_authority_hash=H,p1_custodian_authority_hash=H,dg05_authorization_hash=H,source_commit=C)
            with self.assertRaises(MultiPanelCustodyError):
                advance_state_chain_v2(root,current,GlobalPredictionStateV1.ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED,evidence_kind='WRONG',evidence_hash=H,evidence_path=root/'missing.json')
            mutated_physical=replace(physical,dg05_authorization_hash='f'*64)
            mutated_physical.validate()
            with self.assertRaises(MultiPanelCustodyError):manifest.validate(allowlists,mutated_physical)
            panel=FROZEN_PANEL_ORDER_V2[0];methods=list(dict(census.methods_by_panel)[panel]);methods[0]=replace(methods[0],method_authority_hash=H)
            tampered=replace(census,methods_by_panel=((panel,tuple(methods)),*census.methods_by_panel[1:]))
            with self.assertRaises(MultiPanelCustodyError):tampered.validate()

    def test_v2_failure_receipt_has_no_prediction_fields(self):
        census=self.census_v2();panel,file_id,method_id=census.expected_cells()[0]
        method=census.method(panel,method_id)
        failure=PredictionFailureReceiptV2(panel,file_id,method_id,method.method_authority_hash,method.execution_authority_hash,H,2,H,'SYSTEM_ERROR',H,1,1,C)
        failure.validate(census);document=failure.document()
        self.assertNotIn('prediction_artifact_hash',document);self.assertNotIn('alarm_count',document)
        with self.assertRaises(MultiPanelCustodyError):replace(failure,system_error_count=0).validate(census)

    def test_v2_projection_is_authority_bound_and_label_invariant(self):
        authority=self.allowlists_v2()[FROZEN_PANEL_ORDER_V2[1]];feature=authority.feature_ids[0]
        def project(label):
            readers={authority.timestamp_id:lambda:[1,2],**{name:lambda:[3.,4.] for name in authority.feature_ids},'label':lambda:label}
            return project_attack_columns_v2(header=tuple(readers),column_readers=readers,authority=authority,file_id='f',raw_container_hash=H,source_commit=C)
        first=project([0,0]);second=project(['bad',object()])
        self.assertEqual(first[0],second[0]);self.assertEqual(first[1].projection_hash,second[1].projection_hash)
        with self.assertRaises(MultiPanelCustodyError):
            project_attack_columns_v2(header=(authority.timestamp_id,feature),column_readers={authority.timestamp_id:lambda:[1],feature:lambda:[2]},authority=replace(authority,feature_ids=(feature,'P1_UNKNOWN')),file_id='f',raw_container_hash=H,source_commit=C)

    def test_v2_p1_mapping_authority_and_nested_taint(self):
        provenance=FROZEN_P1_MAPPING_SOURCE_HASHES_V2['22.04']
        authority=FrozenP1MappingAuthorityV2('22.04',tuple(P1MappingEntryV2(name,'P1','EXACT_MATCH',provenance) for name in FROZEN_P1_FEATURES_BY_VERSION_V2['22.04']),provenance,C)
        scenario=OfficialScenarioMetadataV2('22.04','f','s',(authority.entries[0].official_identity,),(),H,H)
        result=classify_p1_scenario_v2(scenario,authority)
        self.assertEqual(result['status'],'P1_ELIGIBLE');self.assertEqual(result['mapping_authority_hash'],authority.document()['self_hash'])
        with self.assertRaises(ValueError):classify_p1_scenario_v2(replace(scenario,dataset_version='21.03'),authority)
        with self.assertRaises(ValueError):assert_method_blind_nested_v2({'nested':{'detector_score':1}})
        with self.assertRaises(ValueError):replace(authority,entries=(P1MappingEntryV2('P1_X','P1','EXACT_MATCH',provenance),)).validate()

    def test_public_allowlist_file_census_and_p1_mapping_bundles_are_exact(self):
        root=Path(__file__).resolve().parents[1]/'research_control_center/validation_v2/multipanel_pre_dg05'
        allowlist_bundle=json.loads((root/'ATTACK_FEATURE_ALLOWLIST_AUTHORITIES_V1.json').read_text(encoding='utf-8'))
        file_bundle=json.loads((root/'ATTACK_FILE_CENSUS_AUTHORITIES_V1.json').read_text(encoding='utf-8'))
        mapping_bundle=json.loads((root/'P1_MAPPING_AUTHORITIES_V1.json').read_text(encoding='utf-8'))
        self.assertEqual(tuple(row['panel_id'] for row in allowlist_bundle['authorities']),FROZEN_PANEL_ORDER_V2)
        expected_files=(('hai-test2.csv',),('test1.csv','test2.csv','test3.csv','test4.csv'),('test1.csv','test2.csv','test3.csv','test4.csv','test5.csv'))
        self.assertEqual(tuple(tuple(row['file_ids']) for row in file_bundle['panels']),expected_files)
        for row in allowlist_bundle['authorities']:
            authority=FrozenFeatureAllowlistAuthorityV2(row['panel_id'],row['dataset_version'],row['timestamp_id'],tuple(row['feature_ids']),row['method_bundle_hash'],row['source_commit'])
            authority.validate();self.assertEqual(authority.document(),row)
        self.assertEqual(tuple(row['dataset_version'] for row in mapping_bundle['authorities']),('23.05','22.04','21.03'))
        for row in mapping_bundle['authorities']:
            authority=FrozenP1MappingAuthorityV2(row['dataset_version'],tuple(P1MappingEntryV2(**entry) for entry in row['entries']),row['official_mapping_source_hash'],row['source_commit'])
            authority.validate();self.assertEqual(authority.document(),row)
            self.assertTrue(all(entry.scope=='P1' and entry.mapping_state=='EXACT_MATCH' for entry in authority.entries))


if __name__=='__main__':unittest.main()
