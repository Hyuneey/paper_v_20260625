"""Append-only private manifest for semantic reduction; does not copy dataset bytes."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal,replay
from paperworks.validation_v2.exp03b_contract_v1 import require
ROOT=Path(__file__).resolve().parents[1]


def main():
    common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=ROOT,text=True).strip()).resolve()
    vault=common.parent.parent/'paper_v_20260625_private_vault';require(vault.exists() and not vault.is_symlink(),'EXISTING_VAULT_REQUIRED')
    prior=vault/'exp03b-bind-001/TASK_PRIVATE_VAULT_MANIFEST.json';prior_raw=prior.read_bytes();replay(json.loads(prior_raw))
    pub=ROOT/'research_control_center/validation_v2/exp03b';private=ROOT/'artifacts/validation_v2/exp03b/private'
    freeze=json.loads((pub/'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json').read_text());replay(freeze)
    records=[]
    for name,h in freeze['private_input_hashes'].items():
        p=private/name;raw=p.read_bytes();require(not p.is_symlink() and sha256(raw).hexdigest()==h,'PRIVATE_CUSTODY_CHANGED')
        records.append({'path':str(p.resolve()),'sha256':h,'bytes':len(raw)})
    manifest=seal({'task':'EXP03B-PAYLOAD-REDUCE-001','records':records,'prior_manifest_file_hash':sha256(prior_raw).hexdigest(),'execution_freeze_hash':freeze['self_hash'],'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,'future_namespaces':['PROVIDER_EXECUTION_V2_AFTER_DG03B_REVISED','POST_TRAIN3_SCI02B_AND_TRAIN4'],'provider_calls':0})
    target=vault/'exp03b-payload-reduce-001/TASK_PRIVATE_VAULT_MANIFEST.json';publish(target,manifest)
    restored=json.loads(target.read_text());replay(restored);require(restored==manifest,'RESTORE_READ_SMOKE')
    publish(pub/'EXP03B_PUBLIC_PRIVATE_INDEX_V2.json',seal({'task':'EXP03B-PAYLOAD-REDUCE-001','private_manifest_hash':manifest['self_hash'],'record_count':len(records),'storage_policy':'SINGLE_COPY_LOCAL_ONLY','second_copy_verified':False,'restore_read_smoke':'PASS','private_paths_published':False,'private_exposures':0}))
    print(json.dumps({'status':'PASS','records':len(records),'storage_policy':'SINGLE_COPY_LOCAL_ONLY','restore_read_smoke':'PASS'}))


if __name__=='__main__':main()
