"""Pre-register and execute normal-only external detector re-instantiation."""
from __future__ import annotations
import argparse, gc, json, pickle, subprocess
from hashlib import sha256
from pathlib import Path
import numpy as np

from paperworks.validation_v2.exp03b_custody_v1 import publish, replay, seal
from paperworks.validation_v2.pca_spe_v2 import PcaSpeConfigV2
from paperworks.validation_v2.isolation_forest_v1 import IsolationForestConfigV1
from paperworks.validation_v2.xver_detector_v1 import (
    ExternalNormalMatrixV1, fit_external_pca_v1, score_external_pca_v1,
    fit_external_if_v1, score_external_if_v1, calibrate_external_v1, alarm_burden_v1,
)
from xver_execution_common import ROOT, load_projection, private_root

OUT=ROOT/'research_control_center/validation_v2/multipanel_pre_dg05'
BASE='3e8799155ede1e4e6b7b835e8e8866c4e21b6d16'
SCIENTIFIC_SOURCE='58b897471e3cbf05c896ae25e19a112d6696708e'
FUSION='587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc'
PORTFOLIOS={
 'HAI23':{'V2A':'ec0b3e2a32d457287cb8b101bec39059e99335be3fd85a3d1fb98668224c52aa','T0':'d95c0bb8234304f2b769e088f4399b6c071b2156982c9e1fadd175dbab5dba02','T2':'bc2b5996989228f198dbcbf38cbedaf38516366f55d5011978ecda94ccf699b6'},
 'HAI22':{'T0':'94f130408361e6b4a8051ed4a72a0ad385e90cb3212e2bf0d27af300f481503f','T2':'b58313cd142256d000f89fd4a40512763b35e6b50752229109646bafc243fb5c'},
 'HAI21':{'T0':'f9cad3c00c422614012b2147f3c21951632f8738ce2d8f9f1108d61ae69d6ef3','T2':'9815c9a66debed593e21364377113d18422a840389d306a4a7648d5f035599dc'}}

def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def document(path):
    value=json.loads(path.read_text(encoding='utf-8'));replay(value);return value
def sha_file(path):
    h=sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def preregister():
    if head()!=BASE:raise ValueError('EXACT_INTEGRATION_BASE_REQUIRED')
    freeze=document(ROOT/'research_control_center/validation_v2/gdn_front_exp04_001/contracts/EXP04_EXECUTION_FREEZE_V1.json')
    mapping=document(ROOT/'research_control_center/validation_v2/dg04_xver_prep/P1_FEATURE_MAPPING_AUTHORITY_V2.json')
    projection=document(ROOT/'research_control_center/validation_v2/dg04_xver_prep/NORMAL_SCHEMA_ONLY_PROJECTION_CONTRACT_V2.json')
    canonical=seal({'schema':'pca_spe_canonical_authority_v1','dataset':'HAI23.05','detector_id':'V2_D0_PCA_SPE_NORMAL_ONLY_V1',
      'feature_universe':'FROZEN_P1_FEATURE_ORDER_37','feature_count':37,'fit':['train1','train2'],'calibration':'train3',
      'standardization':'FIT_POPULATION_MEAN_STD_DDOF0_FLOOR_1E-12','component_policy':'MIN_COMPONENTS_CUMULATIVE_VARIANCE_GE_0.95_WITH_RESIDUAL_DIMENSION',
      'SPE':'SQUARED_L2_RESIDUAL_IN_STANDARDIZED_SPACE','threshold':'0.999_NEAREST_RANK_NO_INTERPOLATION',
      'comparator':'score > threshold','temporal_alignment':'SAME_PHYSICAL_ROW_SECOND','alarm_representation':'DENSE_POINTWISE_BOOLEAN',
      'missing_nonfinite':'FAIL_CLOSED','tie_handling':'EXACT_EIGENVALUE_CUTOFF_TIE_REJECTED',
      'method_config_hash':freeze['preregistrations']['D0_PCA_SPE']['config_hash'],
      'preregistration_hash':freeze['preregistrations']['D0_PCA_SPE']['preregistration_hash'],
      'immutable_HAI23':True,'test_or_attack_accesses':0})
    publish(OUT/'PCA_SPE_CANONICAL_AUTHORITY_V1.json',canonical)
    versions={}
    for short,version in [('HAI22','22.04'),('HAI21','21.03')]:
        features=projection['features'][version]
        rows=[r for r in mapping['rows'] if r['version']==version and r['execution_eligible']]
        if [r['mapped_identity'] for r in rows]!=features:raise ValueError('FEATURE_MAPPING_ORDER_MISMATCH')
        versions[short]={'dataset_version':version,'feature_ids':features,'feature_count':len(features),
          'mapping_status':'SCHEMA_BOUND_PARTIAL_DETECTOR_REPLICATION','fit_splits':['train1','train2'],
          'calibration':('train3' if short=='HAI22' else {'split':'train3','rows':'[0,239370)'}),
          'normal_burden':(['train5','train6'] if short=='HAI22' else {'split':'train3','rows':'[239430,478801)'}),
          'projection_contract_hash':projection['self_hash'],'mapping_hash':mapping['self_hash']}
    prereg=seal({'schema':'multipanel_detector_preregistration_v1','status':'FROZEN_BEFORE_EXTERNAL_DETECTOR_NORMAL_VALUES',
      'integration_base':BASE,'pca_method_config_hash':PcaSpeConfigV2().config_hash,
      'if_method_config_hash':IsolationForestConfigV1().config_hash,'detector_searches':0,'attack_accesses':0,
      'fixed_vs_derived':{'fixed':['algorithm','config','threshold quantile','comparator'],'normal_derived':['mean','scale','loadings','estimator','threshold']},
      'versions':versions,'portfolio_hashes':PORTFOLIOS,'fusion_hash':FUSION})
    publish(OUT/'MULTIPANEL_DETECTOR_PREREGISTRATION_V1.json',prereg)
    print(json.dumps({'status':'PREREGISTERED','canonical':canonical['self_hash'],'prereg':prereg['self_hash']}))

def make_input(version,split,features, *, subset=None):
    matrix,order,row=load_projection(version,split)
    if tuple(order)!=tuple(features):raise ValueError('EXTERNAL_PROJECTION_FEATURE_ORDER')
    if subset is not None:
        start,end=subset;matrix=matrix[start:end]
        projection_hash=sha256((row['projection_hash']+f':{start}:{end}').encode()).hexdigest()
    else:projection_hash=row['projection_hash']
    return ExternalNormalMatrixV1(version,split,projection_hash,tuple(features),matrix)

def persist_private(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        raw=path.read_bytes();existing=pickle.loads(raw)
        if existing['model'].fit_authority['self_hash']!=obj['model'].fit_authority['self_hash'] or existing['threshold']['self_hash']!=obj['threshold']['self_hash']:
            raise ValueError('PRIVATE_EXISTING_SEMANTIC_MISMATCH')
        return sha256(raw).hexdigest(),len(raw)
    raw=pickle.dumps(obj,protocol=5)
    with path.open('xb') as stream:stream.write(raw);stream.flush()
    if sha256(path.read_bytes()).hexdigest()!=sha256(raw).hexdigest():raise ValueError('PRIVATE_REPLAY')
    return sha256(raw).hexdigest(),len(raw)

def execute():
    prereg=document(OUT/'MULTIPANEL_DETECTOR_PREREGISTRATION_V1.json')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('COMMITTED_CLEAN_SOURCE_REQUIRED')
    # Commit A froze the scientific adapter. Later script-only custody recovery
    # must not create a new scientific run identity.
    source=SCIENTIFIC_SOURCE; results={}; private=private_root()/'multipanel_pre_dg05_v1'
    for short,version in [('HAI22','22.04'),('HAI21','21.03')]:
        spec=prereg['versions'][short];features=tuple(spec['feature_ids'])
        train1=make_input(version,'train1',features);train2=make_input(version,'train2',features)
        train3full=make_input(version,'train3',features)
        calibration=train3full if short=='HAI22' else ExternalNormalMatrixV1(version,'train3',sha256((train3full.projection_hash+':0:239370').encode()).hexdigest(),features,train3full.values[:239370])
        methods={}
        pca_path=private/f'{short}_PCA.pkl'
        if pca_path.exists():
            prior=pickle.loads(pca_path.read_bytes());pca,pth=prior['model'],prior['threshold']
            if pca.fit_authority['source_commit']!=source or pca.fit_authority['preregistration_hash']!=prereg['self_hash']:
                raise ValueError('PRIVATE_EXISTING_SCIENTIFIC_AUTHORITY_MISMATCH')
        else:
            pca=fit_external_pca_v1(train1,train2,version=version,feature_ids=features,source_commit=source,preregistration_hash=prereg['self_hash'])
            scores,binding=score_external_pca_v1(pca,calibration,split='train3');pth=calibrate_external_v1(scores,binding,fit_hash=pca.fit_authority['self_hash'],config_hash=PcaSpeConfigV2().config_hash)
        pbytes,psz=persist_private(private/f'{short}_PCA.pkl',{'model':pca,'threshold':pth})
        methods['PCA']={'fit':pca.fit_authority,'threshold_authority_hash':pth['self_hash'],'private_bytes_hash':pbytes,'private_bytes':psz}
        gc.collect()
        if_path=private/f'{short}_IF.pkl'
        if if_path.exists():
            prior=pickle.loads(if_path.read_bytes());forest,ith=prior['model'],prior['threshold']
            if forest.fit_authority['source_commit']!=source or forest.fit_authority['preregistration_hash']!=prereg['self_hash']:
                raise ValueError('PRIVATE_EXISTING_SCIENTIFIC_AUTHORITY_MISMATCH')
        else:
            forest=fit_external_if_v1(train1,train2,version=version,feature_ids=features,source_commit=source,preregistration_hash=prereg['self_hash'])
            scores,binding=score_external_if_v1(forest,calibration,split='train3');ith=calibrate_external_v1(scores,binding,fit_hash=forest.fit_authority['self_hash'],config_hash=IsolationForestConfigV1().config_hash)
        ibytes,isz=persist_private(private/f'{short}_IF.pkl',{'model':forest,'threshold':ith})
        methods['IF']={'fit':forest.fit_authority,'threshold_authority_hash':ith['self_hash'],'private_bytes_hash':ibytes,'private_bytes':isz}
        gc.collect()
        audits={}
        audit_inputs=[]
        if short=='HAI22':
            audit_inputs=[('train5',make_input(version,'train5',features)),('train6',make_input(version,'train6',features))]
        else:
            audit_inputs=[('train3_block_b',ExternalNormalMatrixV1(version,'train3',sha256((train3full.projection_hash+':239430:478801').encode()).hexdigest(),features,train3full.values[239430:478801]))]
        for name,item in audit_inputs:
            split='train3' if name=='train3_block_b' else name
            ps,_=score_external_pca_v1(pca,item,split=split);ifs,_=score_external_if_v1(forest,item,split=split)
            audits[name]={'PCA':alarm_burden_v1(ps,pth['threshold_hex'],file_id=name),'IF':alarm_burden_v1(ifs,ith['threshold_hex'],file_id=name)}
        public={
          'schema':'external_normal_only_detector_authority_v1','detector_status':'FROZEN_NO_ATTACK_PREDICTION',
          'dataset_version':version,'mapping_status':spec['mapping_status'],'feature_ids':list(features),'feature_count':len(features),
          'fit_splits':['train1','train2'],'calibration':spec['calibration'],'normal_audits':audits,
          'PCA':methods['PCA'],'IF':methods['IF'],'private_paths_published':False,'attack_accesses':0,'labels_accessed':0,
          'source_commit':source,'preregistration_hash':prereg['self_hash']}
        # Private hashes identify custody; remove private byte size/path only, not scientific values.
        authority=seal(public);publish(OUT/f'{short}_DETECTOR_AUTHORITY_V1.json',authority);results[short]=authority
        del train1,train2,train3full,calibration,pca,forest;gc.collect()
    index=seal({'schema':'multipanel_detector_execution_result_v1','status':'PASS','source_commit':source,
      'authorities':{k:v['self_hash'] for k,v in results.items()},'attack_predictions':0,'attack_accesses':0,'labels_accessed':0,
      'detector_searches':0,'secondary_IF_ready':True,'private_backup':'SINGLE_COPY_LOCAL_ONLY'})
    publish(OUT/'DETECTOR_EXECUTION_RESULT_V1.json',index)
    print(json.dumps({'status':'PASS','authorities':index['authorities']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preregister',action='store_true');parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if args.preregister==args.execute:raise SystemExit('choose exactly one mode')
    preregister() if args.preregister else execute()
