"""Append private context custody; no label parsing, checkpoints or provider I/O."""
import json,subprocess
from pathlib import Path
from paperworks.data.hai_xver_normal_v1 import sha256_file
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
from paperworks.validation_v2.exp03b_contract_v1 import require
from materialize_xver_normal_v1 import cache_root


def main():
    root=Path(__file__).resolve().parents[1]
    common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=root,text=True).strip()).resolve()
    vault=common.parent.parent/'paper_v_20260625_private_vault'
    require(vault.is_dir() and not vault.is_symlink(),'EXISTING_PRIVATE_VAULT')
    parent=vault/'dg04-xver-prep-001/TASK_PRIVATE_VAULT_MANIFEST_V4.json'
    previous=json.loads(parent.read_text(encoding='utf-8'));replay(previous)
    require(previous['self_hash']=='6945261651671156feb4db483102983f63c7d676941ab184b3fcb7c53f54d157','PARENT_VAULT')
    permitted={'OFFICIAL_NORMAL_CONTAINER_BYTES_ONLY','RAW_CONTAINER_CUSTODY_RECEIPT',
               'LABEL_BLIND_FEATURE_PROJECTION','PROJECTION_RECEIPT','PRIVATE_STAT_AGGREGATE','IMMUTABLE_STAGE_A_BINDING'}
    for prior in previous['records']:
        require(prior['kind'] in permitted,'PARENT_VAULT_SCOPE')
        p=Path(prior['path'])
        require(p.is_file() and not p.is_symlink() and sha256_file(p)==prior['sha256'],'PARENT_PRIVATE_RESTORE')
    pub=root/'research_control_center/validation_v2/xver_normal';records=[]
    for v in ('22','21'):
        bundle=json.loads((pub/f'HAI{v}_GDN_CONTEXT_PROJECTION_RECEIPT_V1.json').read_text());replay(bundle)
        for row in bundle['records']:
            path=cache_root()/'xver_normal_v1/context'/(row['source_file_identity']+'.csv')
            require(path.is_file() and not path.is_symlink() and sha256_file(path)==row['projection_hash'],'CONTEXT_RESTORE')
            receipt_path=path.with_suffix('.receipt.json')
            restored=json.loads(receipt_path.read_text());replay(restored);require(restored==row,'RECEIPT_RESTORE')
            for f,kind in [(path,'LABEL_BLIND_GDN_CONTEXT_PROJECTION'),(receipt_path,'CONTEXT_PROJECTION_RECEIPT')]:
                records.append({'path':str(f.resolve()),'kind':kind,'sha256':sha256_file(f),'bytes':f.stat().st_size})
    plans=[{'relative_authority':p.relative_to(root).as_posix(),'sha256':sha256_file(p)}
           for p in sorted(pub.iterdir()) if p.is_file() and not p.name.startswith('PUBLIC_PRIVATE')]
    manifest=seal({'schema':'task_private_vault_xver_normal_context_v1','task':'HAI-XVER-NORMAL-PREP-001',
        'parent_manifest_hash':previous['self_hash'],'records':records,'public_authorities':plans,
        'parent_private_records_byte_replayed':len(previous['records']),
        'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,
        'status':'BLOCKED_GDN_METHOD_CHANGE_REQUIRED',
        'future_not_materialized':['SCALERS','CHECKPOINTS','SPLIT_PURE_GDN_EVIDENCE','T0_SEMANTICS',
            'T0_NUMERIC_AUTHORITY','T0_FORMAL_V4_PORTFOLIOS','T2_PROVIDER_PACKS','T2_RETRIEVAL_PACKS',
            'TOKEN_COST_PROFILE','PROVIDER_OUTPUTS_AFTER_GATE'],
        'provider_calls':0,'excluded_values_parsed':False,'attack_accesses':0})
    destination=vault/'hai-xver-normal-prep-001/TASK_PRIVATE_VAULT_MANIFEST_V1.json'
    publish(destination,manifest)
    restored=json.loads(destination.read_text());replay(restored);require(restored==manifest,'VAULT_RESTORE')
    index=seal({'schema':'public_xver_normal_private_index_v1','task':'HAI-XVER-NORMAL-PREP-001',
        'parent_manifest_hash':previous['self_hash'],'private_manifest_hash':manifest['self_hash'],
        'record_count':len(records),'public_authority_count':len(plans),'context_projections':4,
        'parent_private_records_byte_replayed':len(previous['records']),
        'restore_read_hash_smoke':'PASS','storage_policy':'SINGLE_COPY_LOCAL_ONLY',
        'second_copy_verified':False,'scientific_GDN_runs':0,'provider_calls':0,
        'excluded_values_parsed':False,'private_exposures':0})
    publish(pub/'PUBLIC_PRIVATE_ARTIFACT_INDEX_V1.json',index)
    print(json.dumps({'status':'PRIVATE_CONTEXT_RESTORE_PASS','records':len(records),'hash':index['self_hash']}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'CUSTODY_FAIL_CLOSED','error_type':type(error).__name__}));raise SystemExit(2)
