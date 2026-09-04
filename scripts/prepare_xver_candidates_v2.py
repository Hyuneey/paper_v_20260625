"""External META portability + unchanged STAT kernels on projected train1/2 only."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import subprocess
import time
import numpy as np
import pandas as pd

from materialize_xver_normal_v1 import cache_root
from paperworks.data.hai_xver_normal_v1 import sha256_file
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
from paperworks.validation_v2.exp03b_contract_v1 import require,digest
from paperworks.v6.common import stable_hash_v1
from paperworks.candidates.metadata_candidate_discovery_v1 import validate_metadata_candidate_result_v1
from paperworks.candidates.statistical_candidate_discovery_v1 import (
    vectorized_file_lagged_correlations_v1, verify_vectorized_parity_v1,
    select_pair_horizon_v1, rank_pair_evidence_v1, PairStatisticalEvidenceV1)

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/dg04_xver_prep'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',choices=('22.04','21.03'),required=True)
    parser.add_argument('--freeze-only',action='store_true');args=parser.parse_args()
    mapping=json.loads((PUB/'P1_FEATURE_MAPPING_AUTHORITY_V1.json').read_text());replay(mapping)
    projection=json.loads((PUB/'NORMAL_SCHEMA_ONLY_PROJECTION_CONTRACT_V2.json').read_text());replay(projection)
    meta_path=ROOT/'docs/task_reports/TASK-039C_META_RESULT.json'
    meta=json.loads(meta_path.read_text())
    require(meta['artifact_hash']==mapping['meta_prior_hash'],'META_PRIOR_IDENTITY')
    require(stable_hash_v1({k:v for k,v in meta.items() if k!='artifact_hash'})==meta['artifact_hash'],'META_SELF_HASH')
    validate_metadata_candidate_result_v1(meta)
    sources=[r[f'hai{args.version[:2]}_identity'] for r in mapping['rows'] if r['role']=='SOURCE' and r[f'hai{args.version[:2]}_mapping']=='EXACT_MATCH']
    targets=[r[f'hai{args.version[:2]}_identity'] for r in mapping['rows'] if r['role']=='TARGET' and r[f'hai{args.version[:2]}_mapping']=='EXACT_MATCH']
    universe=sorted((s,t) for s in sources for t in targets if s!=t)
    portable=sorted((p['source_identity'],p['target_identity']) for p in meta['top20_identities']
                    if (p['source_identity'],p['target_identity']) in universe)
    require(portable,'BLOCKED_META_PORTABILITY')
    contract_path=PUB/f'HAI{args.version[:2]}_CANDIDATE_CONTRACT_V2.json'
    implementation=['scripts/prepare_xver_candidates_v2.py','src/paperworks/candidates/statistical_candidate_discovery_v1.py',
                    'src/paperworks/v6/candidate_discovery_protocol_v1.py',
                    'src/paperworks/candidates/metadata_candidate_discovery_v1.py',
                    'src/paperworks/validation_v2/exp03b_custody_v1.py',
                    'src/paperworks/validation_v2/exp03b_contract_v1.py',
                    'src/paperworks/data/hai_xver_normal_v1.py','scripts/materialize_xver_normal_v1.py']
    config={'schema':'external_candidate_contract_v2','version':args.version,'projection_contract_hash':projection['self_hash'],
         'mapping_hash':mapping['self_hash'],'sources':sources,'targets':targets,'pairs':universe,'portable_meta':portable,
         'meta_authority_hash':mapping['meta_prior_hash'],'meta_file_sha256':sha256(meta_path.read_bytes()).hexdigest(),
         'top_budget':min(20,len(universe)),'normal_splits':['train1','train2'],
         'horizons':[1,5,10,30,60],'score':'UNCHANGED_MIN_ABS_SAME_NONZERO_SIGN_FILE_LOCAL_DIFF_PEARSON',
         'no_padding':True,'GDN_candidate_admission':False,'provider_calls':0,
         'implementation_hashes':{p:sha256((ROOT/p).read_bytes()).hexdigest() for p in implementation}}
    if args.freeze_only:
        publish(contract_path,seal(config));print(json.dumps({'status':'CANDIDATE_CONTRACT_FROZEN','version':args.version}));return
    contract=json.loads(contract_path.read_text());replay(contract)
    require(digest(config)==contract['self_hash'],'CANDIDATE_CONTRACT_DRIFT')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    custody_path=PUB/f'HAI{args.version[:2]}_NORMAL_PROJECTION_RECEIPT_V2.json'
    for path in [contract_path,meta_path,PUB/'P1_FEATURE_MAPPING_AUTHORITY_V1.json',
                 PUB/'NORMAL_SCHEMA_ONLY_PROJECTION_CONTRACT_V2.json',custody_path]+[ROOT/p for p in implementation]:
        require(path.read_bytes()==subprocess.check_output(['git','show',head+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT),'CANDIDATE_CODE_NOT_COMMITTED')
    verify_vectorized_parity_v1()
    custody=json.loads(custody_path.read_text());replay(custody)
    require(custody['status']=='NORMAL_ONLY_CUSTODY_READY' and custody['contract_hash']==projection['self_hash'] and
            custody['version']==args.version and custody['label_values_parsed'] is False,'NORMAL_CUSTODY')
    require(len({r['source_file_identity'] for r in custody['records']})==len(custody['records']), 'DUPLICATE_CUSTODY_SPLIT')
    matrices=[];inputs=[];start=time.perf_counter()
    for split in ('train1','train2'):
        symbolic=f'HAI{args.version[:2]}_{split.upper()}'
        receipt=next(r for r in custody['records'] if r['source_file_identity']==symbolic);replay(receipt)
        require(receipt['dataset_version']==args.version and receipt['feature_allowlist_hash']==digest(projection['features'][args.version]) and
                receipt['projected_feature_identities']==projection['features'][args.version] and receipt['label_values_parsed'] is False,'SPLIT_FEATURE_CUSTODY')
        path=cache_root()/'projections_v2'/f'{symbolic}.csv'
        require(sha256_file(path)==receipt['projection_hash'],'PROJECTION_HASH')
        # This CSV contains exclusively approved fields; raw containers are never opened.
        frame=pd.read_csv(path,usecols=sources+targets,dtype='float64',float_precision='round_trip')
        require(len(frame)==receipt['row_count'] and np.isfinite(frame.to_numpy()).all(),'PROJECTED_FRAME')
        matrices.append(vectorized_file_lagged_correlations_v1(source_values=frame[sources].to_numpy(),target_values=frame[targets].to_numpy()))
        inputs.append(receipt['self_hash'])
        del frame
    evidence=[]
    for s,t in universe:
        i,j=sources.index(s),targets.index(t)
        correlations={h:(float(matrices[0][h][i,j]),float(matrices[1][h][i,j])) for h in contract['horizons']}
        records,selection,sign=select_pair_horizon_v1(correlations)
        evidence.append(PairStatisticalEvidenceV1(s,t,records,selection,sign))
    ranked=rank_pair_evidence_v1(evidence)
    selected=[(e.source,e.target) for e in ranked if e.supported][:contract['top_budget']]
    union=sorted(set(portable)|set(selected))
    private=seal({'contract_hash':contract['self_hash'],'input_receipt_hashes':inputs,
                  'ranked_evidence':[e.to_private_dict(audit_rank=i+1) for i,e in enumerate(ranked)]})
    publish(cache_root()/'candidate_v2'/f'HAI{args.version[:2]}_STAT_PRIVATE.json',private)
    authority=seal({'schema':'external_META_STAT_candidate_authority_v2','version':args.version,'source_commit':head,
        'contract_hash':contract['self_hash'],'custody_hash':custody['self_hash'],'private_STAT_hash':private['self_hash'],
        'meta_prior_hash':mapping['meta_prior_hash'],'source_count':len(sources),'target_count':len(targets),
        'universe_count':len(universe),'META_count':len(portable),'STAT_count':len(selected),'candidate_count':len(union),
        'STAT_requested_budget':contract['top_budget'],'STAT_supported_count':sum(e.supported for e in ranked),
        'STAT_shortfall_count':contract['top_budget']-len(selected),
        'pairs':[{'source':s,'target':t,'provenance':('META_STAT' if (s,t) in portable and (s,t) in selected else 'META' if (s,t) in portable else 'STAT')} for s,t in union],
        'STAT_top_pairs':[{'source':s,'target':t} for s,t in selected],
        'normal_splits':['train1','train2'],'kernel_synthetic_parity':'PASS','wall_seconds':time.perf_counter()-start,
        'no_new_META':True,'GDN_admission':False,'attack_accesses':0,'provider_calls':0,'private_exposures':0})
    publish(PUB/f'HAI{args.version[:2]}_META_STAT_CANDIDATE_AUTHORITY_V2.json',authority)
    print(json.dumps({k:authority[k] for k in ('version','META_count','STAT_count','candidate_count','self_hash')}))


if __name__=='__main__':
    try: main()
    except Exception as error:
        code=str(error) if isinstance(error,ValueError) and str(error).replace('_','').isalnum() else type(error).__name__
        print(json.dumps({'status':'BLOCKED_NORMAL_DATA_CUSTODY','issue':code}),flush=True);raise SystemExit(2)
