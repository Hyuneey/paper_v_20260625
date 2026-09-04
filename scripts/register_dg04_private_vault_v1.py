"""Register exact new portfolio manifests and public preparation; no dataset access."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal,replay
from paperworks.validation_v2.exp03b_contract_v1 import require


def main():
    root=Path(__file__).resolve().parents[1]
    common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=root,text=True).strip()).resolve()
    vault=common.parent.parent/'paper_v_20260625_private_vault'
    require(vault.exists() and not vault.is_symlink(),'EXISTING_VAULT_REQUIRED')
    prior=vault/'gdn-front-exp04-001/PRIVATE_ARTIFACT_MANIFEST.json'
    prior_hash=sha256(prior.read_bytes()).hexdigest()
    private=root/'artifacts/validation_v2/dg04_xver_prep/private'
    records=[]
    for name in ('T0_PORTFOLIO_BINDING.json','T2_PORTFOLIO_BINDING.json'):
        path=private/name
        require(subprocess.run(['git','check-ignore','--quiet',str(path)],cwd=root).returncode==0,'PRIVATE_NOT_IGNORED')
        require(not path.is_symlink(),'PRIVATE_SYMLINK')
        content=path.read_bytes();records.append({'path':str(path.resolve()),'sha256':sha256(content).hexdigest(),'bytes':len(content)})
    pub=root/'research_control_center/validation_v2/dg04_xver_prep'
    plans=[]
    for path in sorted(pub.iterdir()):
        if path.is_file() and path.suffix in ('.json','.md','.csv') and not path.name.startswith('PUBLIC_PRIVATE_INDEX_'):
            plans.append({'relative_authority':path.relative_to(root).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest()})
    for name in ('PANEL_REGISTRY_V2.csv','IMPLEMENTATION_TASK_INDEX_V2.csv'):
        path=root/'research_control_center/validation_v2/evaluation_expansion'/name
        plans.append({'relative_authority':path.relative_to(root).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest()})
    previous=json.loads((vault/'dg04-xver-prep-001/TASK_PRIVATE_VAULT_MANIFEST_V2.json').read_text(encoding='utf-8'));replay(previous)
    manifest=seal({'task':'DG04-XVER-PREP-001','scope':'VAULT_REGISTRATION_ONLY','supersedes_manifest_hash':previous['self_hash'],'status':'STAGE_A_COMPLETE_STAGE_B_BLOCKED',
        'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,'prior_manifest_hash':prior_hash,
        'records':records,'public_preparation_authorities':plans,
        'normal_acquisition_state':'Two official train1 containers identity checked; schema guard stopped. No additional normal cache read for this registration.',
        'future_requirements':['NORMAL_FEATURE_ONLY_CUSTODY','EXTERNAL_SPLIT_PURE_GDN','EXTERNAL_T0','DG03C_PROVIDER_PACKS'],
        'dataset_file_reads':0,'provider_calls':0})
    path=vault/'dg04-xver-prep-001/TASK_PRIVATE_VAULT_MANIFEST_V3.json'
    publish(path,manifest);restored=json.loads(path.read_text(encoding='utf-8'));replay(restored)
    require(restored==manifest,'RESTORE_READ_SMOKE')
    index=seal({'task':'DG04-XVER-PREP-001','scope':'VAULT_REGISTRATION_ONLY','supersedes':'PUBLIC_PRIVATE_INDEX_V2.json','private_manifest_hash':manifest['self_hash'],'record_count':len(records),
        'public_plan_count':len(plans),'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,
        'restore_read_smoke':'PASS','dataset_file_reads':0,
        'task_level_normal_container_traversal':'TWO_OFFICIAL_NORMAL_TRAIN1_CONTAINERS_PRIOR_TO_VAULT_REGISTRATION',
        'scope_note':'The V1 zero-read counter described manifest registration, not the whole task; this successor makes the scope explicit.',
        'private_paths_published':False,'private_exposures':0})
    publish(pub/'PUBLIC_PRIVATE_INDEX_V3.json',index)
    print(json.dumps({'status':'MANIFEST_RESTORE_PASS','record_count':len(records),'storage_policy':index['storage_policy']}))


if __name__=='__main__':main()
