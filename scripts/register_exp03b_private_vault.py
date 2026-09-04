"""Register exact task-local preparation artifacts; no raw dataset or credential read."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal,replay
from paperworks.validation_v2.exp03b_contract_v1 import require

def main():
    root=Path(__file__).resolve().parents[1]
    common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=root,text=True).strip()).resolve()
    vault=common.parent.parent/'paper_v_20260625_private_vault'
    require(vault.exists() and not vault.is_symlink(),'EXISTING_VAULT_REQUIRED')
    prior=vault/'gdn-front-exp04-001/PRIVATE_ARTIFACT_MANIFEST.json'
    prior_hash=sha256(prior.read_bytes()).hexdigest()
    private=root/'artifacts/validation_v2/exp03b/private'
    require(subprocess.run(['git','check-ignore','--quiet',str(private)],cwd=root).returncode==0,'PRIVATE_NOT_IGNORED')
    records=[]
    for p in sorted(private.rglob('*.json')):
        require(not p.is_symlink(),'PRIVATE_SYMLINK')
        content=p.read_bytes();records.append({'path':str(p.resolve()),'sha256':sha256(content).hexdigest(),'bytes':len(content)})
    document=seal({'task':'EXP03B-BIND-001','storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,'prior_manifest_hash':prior_hash,'records':records,'future_requirements':['PROVIDER_CALLS_RESPONSES','HIDDEN_EVALUATION_GUARD','PROSPECTIVE_AGENTIC_V3_AFTER_DG04'],'raw_scientific_file_reads':0})
    target=vault/'exp03b-bind-001/TASK_PRIVATE_VAULT_MANIFEST.json'
    publish(target,document);restored=json.loads(target.read_text());replay(restored);require(restored==document,'RESTORE_READ_SMOKE')
    publish(root/'research_control_center/validation_v2/exp03b/EXP03B_PUBLIC_PRIVATE_INDEX_V1.json',seal({'task':'EXP03B-BIND-001','private_manifest_hash':document['self_hash'],'record_count':len(records),'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,'restore_read_smoke':'PASS','private_paths_published':False,'provider_calls':0,'private_exposures':0}))
    print(json.dumps({'status':'PASS','records':len(records),'storage_policy':'SINGLE_COPY_LOCAL_ONLY','private_exposures':0}))

if __name__=='__main__':main()
