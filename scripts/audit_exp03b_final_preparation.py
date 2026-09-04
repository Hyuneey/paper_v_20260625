"""Read-only authority, private hash and frozen-input closure; no scientific rerun."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from paperworks.validation_v2.exp03b_custody_v1 import replay
from paperworks.validation_v2.exp03b_contract_v1 import require
from audit_exp03b_preparation_gate_v1 import audit
ROOT=Path(__file__).resolve().parents[1]
def main():
    public=ROOT/'research_control_center/validation_v2/exp03b';private=ROOT/'artifacts/validation_v2/exp03b/private'
    frozen=json.loads((public/'EXP03B_FINAL_PREPARATION_FREEZE_V2.json').read_text());replay(frozen)
    for name,h in frozen['implementation_hashes'].items():require(sha256((ROOT/name).read_bytes()).hexdigest()==h,'FINAL_CODE_HASH')
    for name,h in frozen['private_input_hashes'].items():require(sha256((private/name).read_bytes()).hexdigest()==h,'PRIVATE_INPUT_HASH')
    for p in public.glob('*.json'):
        value=json.loads(p.read_text())
        if 'self_hash' in value:replay(value)
    require(subprocess.run(['git','check-ignore','--quiet',str(private)],cwd=ROOT).returncode==0,'PRIVATE_IGNORE')
    require(not subprocess.check_output(['git','ls-files','--',str(private)],cwd=ROOT).strip(),'PRIVATE_TRACKED')
    manifest=json.loads((ROOT/'research_control_center/validation_v2/PILOT_V1_PRESERVATION_MANIFEST.json').read_text())
    base=subprocess.check_output(['git','ls-tree','-r','-z',manifest['authority_commit']],cwd=ROOT)
    index=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)
    entries={x.split(b'\t',1)[1]:x.split(b'\t',1)[0].split()[1] for x in index.split(b'\0') if x}
    expected={x.split(b'\t',1)[1]:x.split(b'\t',1)[0].split()[2] for x in base.split(b'\0') if x and b' blob ' in x.split(b'\t',1)[0]}
    require(len(expected)==3021 and all(entries.get(k)==v for k,v in expected.items()),'PILOT_INDEX_CHANGED')
    changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    require(not any(p.encode() in expected for p in changed),'PILOT_WORKTREE_CHANGED')
    for ref in (manifest['authority_ref'],manifest['immutable_tag']):require(subprocess.check_output(['git','rev-parse',ref+'^{commit}'],cwd=ROOT,text=True).strip()==manifest['authority_commit'],'PILOT_REF_CHANGED')
    preservation=audit(ROOT)
    require(not (private/'provider_execution_v1').exists(),'UNEXPECTED_PROVIDER_EXECUTION')
    print(json.dumps({'status':'PASS','PILOT_V1_blobs':3021,'protected_V2_blobs':preservation['protected_public_blob_count'],'private_hash_records':len(frozen['private_input_hashes']),'implementation_hashes':len(frozen['implementation_hashes']),'provider_calls':0,'test1_accesses':0,'test2_accesses':0,'labels':0,'private_exposures':0}))
if __name__=='__main__':main()
