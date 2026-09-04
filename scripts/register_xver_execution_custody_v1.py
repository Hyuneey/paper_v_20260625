"""Append an execution-vault manifest from exact task-owned namespaces only."""
import json
import subprocess
from pathlib import Path
from xver_execution_common import ROOT, PUB, private_root, document, publish, seal, require, sha256_file


def main():
    common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=ROOT,text=True).strip()).resolve()
    vault=common.parent.parent/'paper_v_20260625_private_vault'
    parent_path=vault/'hai-xver-normal-prep-001/TASK_PRIVATE_VAULT_MANIFEST_V1.json'
    parent=document(parent_path)
    require(parent['storage_policy']=='SINGLE_COPY_LOCAL_ONLY' and not parent['second_copy_verified'],'BACKUP_STATUS')
    for r in parent['records']:require(sha256_file(Path(r['path']))==r['sha256'],'PARENT_PRIVATE_REPLAY')
    records=[];identities=set()
    def add(path,kind,expected=None):
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(private_root().resolve()),'EXECUTION_PRIVATE_NAMESPACE')
        h=sha256_file(path)
        if expected:require(h==expected,'EXECUTION_CUSTODY_HASH')
        relative=path.relative_to(private_root()).as_posix();require(relative not in identities,'DUPLICATE_PRIVATE_RECORD');identities.add(relative)
        records.append({'path':str(path.resolve()),'symbolic_id':relative,'kind':kind,'sha256':h,'bytes':path.stat().st_size})
    for version in ('22.04','21.03'):
        for split in ('train1','train2'):
            for seed in (11,23,37):
                r=document(PUB/'runs'/f'HAI{version[:2]}_{split.upper()}_SEED{seed}_RECEIPT_V1.json')
                require(r['scope']=='SCIENTIFIC' and r['status']=='PASS','SCIENTIFIC_RUN_COMPLETE')
                directory=private_root()/'runs'/r['run_identity_hash']
                for name,kind,h in (('checkpoint.pt','CHECKPOINT_WITH_SCALER_CONFIG_AND_PURGED_COORDINATES',r['checkpoint_sha256']),('global.json','SPLIT_PURE_GLOBAL_GDN',r['global_hash']),('auxiliary_event.json','AUXILIARY_EVENT_ONLY',r['auxiliary_hash']),('identity.json','RUN_IDENTITY',None),('checkpoint_receipt.json','CHECKPOINT_CUSTODY',None)):
                    add(directory/name,kind,h)
                for path in sorted(directory.glob('attempt_*.json')):add(path,'APPEND_ONLY_ATTEMPT_RECORD')
        directory=private_root()/'semantic'/('HAI'+version[:2])
        closure=document(directory/'PROVIDER_PREPARATION_FROZEN.json')
        require(closure['provider_calls_authorized'] is False,'PROVIDER_GATE')
        for path in sorted(directory.rglob('*.json')):add(path,'NORMAL_SEMANTIC_NUMERIC_OR_PROVIDER_PREPARATION')
    manifest=seal({'schema':'task_private_vault_xver_execution_v2','task':'HAI-XVER-NORMAL-PREP-001','parent_manifest_hash':parent['self_hash'],'records':records,'scientific_runs':12,'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,'future_namespaces':['HAI22_T2_PROVIDER_RESPONSES_AFTER_APPROVAL','HAI21_T2_PROVIDER_RESPONSES_AFTER_APPROVAL','FUTURE_T2_PORTFOLIOS','PREDICTIONS_SCENARIOS_ELIGIBILITY_AFTER_DG05'],'provider_calls':0,'attack_accesses':0,'excluded_label_values_parsed':False})
    destination=parent_path.with_name('TASK_PRIVATE_VAULT_MANIFEST_V2.json');publish(destination,manifest)
    restored=document(destination)
    for r in restored['records']:require(sha256_file(Path(r['path']))==r['sha256'],'PRIVATE_RESTORE_HASH')
    index=seal({'schema':'public_xver_execution_private_index_v2','private_manifest_hash':manifest['self_hash'],'parent_manifest_hash':parent['self_hash'],'record_count':len(records),'scientific_runs':12,'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,'restore_read_hash_smoke':'PASS','provider_calls':0,'credential_reads':0,'attack_accesses':0,'private_paths_published':0})
    publish(PUB/'PUBLIC_PRIVATE_EXECUTION_INDEX_V2.json',index)
    print(json.dumps({'status':'PRIVATE_VAULT_RESTORE_PASS','record_count':len(records),'manifest_hash':manifest['self_hash']}))


if __name__=='__main__':main()
