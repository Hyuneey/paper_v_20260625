"""Read-only exact local resume/custody replay. Never deserialize normal rows."""
import json
import subprocess
from pathlib import Path
from hashlib import sha256
from paperworks.validation_v2.exp03b_custody_v1 import replay
from paperworks.validation_v2.exp03b_contract_v1 import require
from paperworks.data.hai_xver_normal_v1 import sha256_file
from xver_execution_common import cache_root

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/xver_normal'
BASE='dd93c43d539182eb6d3bc1b38bc8066f578c4bb2'


def replay_inputs():
    require(subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT).returncode==0,'LOCAL_RESUME_ANCESTRY')
    def public(path):
        payload=path.read_bytes()
        require(payload==subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT),'CURRENT_AUTHORITY_BYTES')
        value=json.loads(payload);replay(value);return value
    binding=public(PUB/'GDN_SEPARATED_EVIDENCE_BINDING_V1.json')
    for name,h in binding['implementation_hashes'].items():
        require(sha256((ROOT/name).read_bytes()).hexdigest()==h,'BINDING_IMPLEMENTATION')
    for name,h in binding['dependencies'].items():require(public(PUB/name)['self_hash']==h,'BINDING_DEPENDENCY')
    parent=ROOT/'research_control_center/validation_v2/dg04_xver_prep'
    for arm,expected in [('T0','d95c0bb8234304f2b769e088f4399b6c071b2156982c9e1fadd175dbab5dba02'),
                         ('T2','bc2b5996989228f198dbcbf38cbedaf38516366f55d5011978ecda94ccf699b6')]:
        require(public(parent/f'{arm}_HELDOUT_CANDIDATE_PORTFOLIO_V1.json')['self_hash']==expected,'STAGE_A_PORTFOLIO')
    public(parent/'FINAL_METHOD_LOCK_V1.json')
    counts={}
    for v in ('22','21'):
        candidate=public(parent/f'HAI{v}_META_STAT_CANDIDATE_AUTHORITY_V2.json')
        require(len(candidate['pairs'])==len({(r['source'],r['target']) for r in candidate['pairs']}),'CANDIDATE_DUPLICATES')
        counts[v]=len(candidate['pairs'])
        for name,folder in [(f'HAI{v}_NORMAL_PROJECTION_RECEIPT_V2.json','projections_v2'),
                            (f'HAI{v}_GDN_CONTEXT_PROJECTION_RECEIPT_V1.json','xver_normal_v1/context')]:
            bundle=public((parent if folder=='projections_v2' else PUB)/name)
            for row in bundle['records']:
                replay(row)
                require(row['label_values_parsed'] is False and row['label_values_validated'] is False and row['label_values_used'] is False,'LABEL_CUSTODY')
                path=cache_root()/folder/(row['source_file_identity']+'.csv')
                require(path.is_file() and not path.is_symlink() and sha256_file(path)==row['projection_hash'],'PROJECTION_BYTES')
    common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=ROOT,text=True).strip()).resolve()
    vault=common.parent.parent/'paper_v_20260625_private_vault'
    index=public(PUB/'PUBLIC_PRIVATE_ARTIFACT_INDEX_V1.json')
    manifest=json.loads((vault/'hai-xver-normal-prep-001/TASK_PRIVATE_VAULT_MANIFEST_V1.json').read_text());replay(manifest)
    require(manifest['self_hash']==index['private_manifest_hash'],'VAULT_MANIFEST_HASH')
    for row in manifest['records']:
        require(row['kind'] in ('LABEL_BLIND_GDN_CONTEXT_PROJECTION','CONTEXT_PROJECTION_RECEIPT'),'VAULT_RECORD_KIND')
        path=Path(row['path']);require(not path.is_symlink() and sha256_file(path)==row['sha256'],'VAULT_PRIVATE_HASH')
    for row in manifest['public_authorities']:
        require(sha256_file(ROOT/row['relative_authority'])==row['sha256'],'VAULT_PUBLIC_HASH')
    return {'status':'PASS','candidate_counts':counts,'binding_hash':binding['self_hash'],
            'private_vault_records':len(manifest['records']),'feature_values_parsed':False,
            'label_values_parsed':False,'provider_calls':0,'credential_reads':0,'attack_accesses':0}


if __name__=='__main__':
    try:print(json.dumps(replay_inputs()))
    except Exception as error:
        print(json.dumps({'status':'BLOCKED_CURRENT_AUTHORITY_REPLAY','error_type':type(error).__name__,
            'code':str(error) if type(error) is ValueError and str(error).replace('_','').isalnum() else 'REDACTED'}));raise SystemExit(2)
