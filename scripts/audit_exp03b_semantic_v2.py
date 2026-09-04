"""Read-only reduced preparation closure. No raw feature/provider/credential access."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from paperworks.validation_v2.exp03b_custody_v1 import replay
from paperworks.validation_v2.exp03b_contract_v1 import require,digest
from paperworks.validation_v2.exp03b_prompt_v2 import validate_projection,request_body
from paperworks.validation_v2.exp03b_firewall_v2 import assert_clean
ROOT=Path(__file__).resolve().parents[1];PUB=ROOT/'research_control_center/validation_v2/exp03b';PRIVATE=ROOT/'artifacts/validation_v2/exp03b/private'


def main():
    freeze=json.loads((PUB/'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json').read_text());replay(freeze)
    old=json.loads((PUB/'EXP03B_FINAL_PREPARATION_FREEZE_V2.json').read_text());replay(old)
    for name,h in freeze['implementation_hashes'].items():require(sha256((ROOT/name).read_bytes()).hexdigest()==h,'NEW_CODE_HASH')
    for name,h in {**old['private_input_hashes'],**freeze['private_input_hashes']}.items():require(sha256((PRIVATE/name).read_bytes()).hexdigest()==h,'PRIVATE_HASH')
    before=subprocess.check_output(['git','ls-tree','-r','--name-only','6f1ae35eb0a8ca0143c1e3e5cb0b752a500e09d1','--','research_control_center/validation_v2/exp03b'],cwd=ROOT,text=True).splitlines()
    for name in before:
        original=subprocess.check_output(['git','show','6f1ae35eb0a8ca0143c1e3e5cb0b752a500e09d1:'+name],cwd=ROOT)
        require(original==(ROOT/name).read_bytes(),'EXP03B_V1_PUBLIC_CHANGED')
    cohort=json.loads((PUB/'EXP03B_COHORT_AUTHORITY_V1.json').read_text());replay(cohort)
    for pair in cohort['pairs']:
        cid=pair['candidate_id'];new=json.loads((PRIVATE/f'semantic_v2/train1/provider/{cid}.json').read_text());prior=json.loads((PRIVATE/f'train1/provider/{cid}.json').read_text())
        validate_projection(new);assert_clean(new)
        for key in new:require(new[key]==prior[key],'EVIDENCE_SEMANTIC_CHANGE')
        request=json.loads((PRIVATE/f'semantic_v2/train1/requests/{cid}.json').read_text());require(request==request_body(new),'FROZEN_REQUEST_REPLAY')
    for path in PUB.glob('*.json'):
        value=json.loads(path.read_text())
        if 'self_hash' in value:replay(value)
    budget=json.loads((PUB/'EXP03B_PROVIDER_BUDGET_V2.json').read_text())
    require(budget['self_hash']==freeze['provider_budget_hash'] and budget['config_hash']==freeze['provider_config_hash'],'BUDGET_FREEZE_BINDING')
    require(budget['N']==cohort['count'] and budget['maximum_calls']==budget['N']*budget['R']*7,'CALL_SCHEDULE')
    require(budget['maximum_input_tokens']==budget['N']*budget['R']*(5*budget['phase_input_caps']['initial']+2*budget['phase_input_caps']['repair']),'INPUT_ARITHMETIC')
    require(subprocess.run(['git','check-ignore','--quiet',str(PRIVATE)],cwd=ROOT).returncode==0 and not subprocess.check_output(['git','ls-files','--',str(PRIVATE)],cwd=ROOT).strip(),'PRIVATE_TRACKING')
    require(not (PRIVATE/'provider_execution_v1').exists() and not (PRIVATE/'provider_execution_v2').exists(),'UNAUTHORIZED_PROVIDER_EXECUTION')
    print(json.dumps({'status':'PASS','cohort':cohort['count'],'preserved_V1_public_files':len(before),'preserved_private_hashes':len(old['private_input_hashes']),'revised_private_hashes':len(freeze['private_input_hashes']),'implementation_hashes':len(freeze['implementation_hashes']),'payload_semantic_equality':'PASS','provider_calls':0,'credential_reads':0,'raw_data_reads':0,'test1':0,'test2':0,'private_exposures':0}))


if __name__=='__main__':main()
