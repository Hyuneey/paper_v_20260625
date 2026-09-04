"""Reopen/hash exact normal containers/projections and append vault manifest V4.

Raw normal byte hashing is authorized. No excluded field is decoded or parsed.
"""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from materialize_xver_normal_v1 import cache_root
from paperworks.data.hai_xver_normal_v1 import sha256_file
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal,replay
from paperworks.validation_v2.exp03b_contract_v1 import require


def main():
    root=Path(__file__).resolve().parents[1]
    common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=root,text=True).strip()).resolve()
    vault=common.parent.parent/'paper_v_20260625_private_vault'
    require(vault.exists() and not vault.is_symlink(),'EXISTING_VAULT_REQUIRED')
    folder=vault/'dg04-xver-prep-001'
    previous=json.loads((folder/'TASK_PRIVATE_VAULT_MANIFEST_V3.json').read_text(encoding='utf-8'));replay(previous)
    pub=root/'research_control_center/validation_v2/dg04_xver_prep';records=[]
    def add(path,kind,expected=None):
        require(path.is_file() and not path.is_symlink(),'PRIVATE_FILE_REQUIRED')
        h=sha256_file(path)
        if expected:require(h==expected,'PRIVATE_RESTORE_HASH')
        records.append({'path':str(path.resolve()),'kind':kind,'sha256':h,'bytes':path.stat().st_size})
    cache=cache_root()
    for version in ('22.04','21.03'):
        custody=json.loads((pub/f'HAI{version[:2]}_NORMAL_PROJECTION_RECEIPT_V2.json').read_text());replay(custody)
        for row in custody['records']:
            replay(row)
            raw=cache/row['official_source_identity']['materialized_relative_path']
            add(raw,'OFFICIAL_NORMAL_CONTAINER_BYTES_ONLY',row['raw_container_hash'])
            add(raw.with_suffix('.custody.json'),'RAW_CONTAINER_CUSTODY_RECEIPT')
            projection=cache/'projections_v2'/f"{row['source_file_identity']}.csv"
            add(projection,'LABEL_BLIND_FEATURE_PROJECTION',row['projection_hash'])
            receipt_path=projection.with_suffix('.receipt.json')
            private_receipt=json.loads(receipt_path.read_text());replay(private_receipt)
            require(private_receipt==row,'PRIVATE_PUBLIC_RECEIPT_REPLAY')
            add(receipt_path,'PROJECTION_RECEIPT')
        path=cache/'candidate_v2'/f'HAI{version[:2]}_STAT_PRIVATE.json'
        value=json.loads(path.read_text());replay(value)
        authority=json.loads((pub/f'HAI{version[:2]}_META_STAT_CANDIDATE_AUTHORITY_V2.json').read_text());replay(authority)
        require(value['self_hash']==authority['private_STAT_hash'],'STAT_PRIVATE_CUSTODY')
        add(path,'PRIVATE_STAT_AGGREGATE')
    for arm in ('T0','T2'):
        path=root/f'artifacts/validation_v2/dg04_xver_prep/private/{arm}_PORTFOLIO_BINDING.json'
        require(subprocess.run(['git','check-ignore','--quiet',str(path)],cwd=root).returncode==0,'PRIVATE_NOT_IGNORED')
        add(path,'IMMUTABLE_STAGE_A_BINDING')
    plans=[{'relative_authority':p.relative_to(root).as_posix(),'sha256':sha256_file(p)} for p in sorted(pub.iterdir())
           if p.is_file() and p.suffix in ('.json','.csv','.md') and not p.name.startswith('PUBLIC_PRIVATE_INDEX_')]
    for name in ('PANEL_REGISTRY_V2.csv','IMPLEMENTATION_TASK_INDEX_V2.csv'):
        p=root/'research_control_center/validation_v2/evaluation_expansion'/name
        plans.append({'relative_authority':p.relative_to(root).as_posix(),'sha256':sha256_file(p)})
    manifest=seal({'schema':'task_private_vault_manifest_v4','task':'DG04-XVER-PREP-001',
        'supersedes_manifest_hash':previous['self_hash'],'status':'BLOCKED_PENDING_HAI_XVER_NORMAL_PREP',
        'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,'records':records,
        'public_preparation_authorities':plans,'raw_normal_files_hashed':9,'excluded_values_parsed':False,
        'future_requirements':['GDN_CONTEXT_AND_CHECKPOINTS','SPLIT_PURE_SEMANTIC_EVIDENCE','EXTERNAL_T0_T2_PORTFOLIOS',
                               'PROVIDER_PROMPTS_RESPONSES_AFTER_APPROVAL','HELDOUT_PREDICTIONS_AFTER_DG05','OPAQUE_SCENARIO_ELIGIBILITY'],
        'provider_calls':0,'attack_accesses':0})
    path=folder/'TASK_PRIVATE_VAULT_MANIFEST_V4.json';publish(path,manifest)
    restored=json.loads(path.read_text());replay(restored);require(restored==manifest,'MANIFEST_RESTORE')
    index=seal({'schema':'public_private_index_v4','task':'DG04-XVER-PREP-001','supersedes':'PUBLIC_PRIVATE_INDEX_V3.json',
        'private_manifest_hash':manifest['self_hash'],'record_count':len(records),'public_plan_count':len(plans),
        'raw_normal_files_hashed':9,'label_blind_projections_replayed':9,'private_STAT_authorities_replayed':2,
        'restore_read_hash_smoke':'PASS','storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,
        'excluded_values_parsed':False,'attack_accesses':0,'provider_calls':0,'private_exposures':0})
    publish(pub/'PUBLIC_PRIVATE_INDEX_V4.json',index)
    print(json.dumps({'status':'VAULT_RESTORE_PASS','records':len(records),'plans':len(plans),'hash':index['self_hash']}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        code=str(error) if isinstance(error,ValueError) and str(error).replace('_','').isalnum() else type(error).__name__
        print(json.dumps({'status':'BLOCKED_NORMAL_DATA_CUSTODY','issue':code}));raise SystemExit(2)
