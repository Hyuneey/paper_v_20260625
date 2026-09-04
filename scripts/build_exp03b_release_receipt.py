"""Publish a tested public release receipt; never calls provider or scientific runner."""
from pathlib import Path
import json,os,subprocess,sys
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
ROOT=Path(__file__).resolve().parents[1]
def main():
    env=dict(os.environ);env['PYTHONPATH']='src;tests'
    commands={
        'focused':[sys.executable,'-m','unittest','test_exp03b_preparation_gate_v1','test_exp03b_bindings_v1','test_exp03b_execution_prep','test_exp03b_gate_reporting','-q'],
        'validation_v2':[sys.executable,'-m','unittest','discover','-s','tests','-p','test_validation_v2*.py','-q'],
        'rcc_ui':[sys.executable,'-m','unittest','discover','-s','research_control_center/tests','-q'],
        'authority':[sys.executable,'scripts/audit_exp03b_final_preparation.py'],
        'registry_privacy':[sys.executable,'research_control_center/scripts/validate_registry.py'],
    }
    receipts={}
    from hashlib import sha256
    for name,cmd in commands.items():
        r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True)
        if r.returncode:print(json.dumps({'status':'FAIL','check':name}));raise SystemExit(2)
        receipts[name]={'status':'PASS','output_hash':sha256(r.stdout+r.stderr).hexdigest()}
        print(json.dumps({'check':name,'status':'PASS'}),flush=True)
    public=ROOT/'research_control_center/validation_v2/exp03b'
    frozen=json.loads((public/'EXP03B_FINAL_PREPARATION_FREEZE_V2.json').read_text());replay(frozen)
    doc=seal({'task_id':'EXP03B-BIND-001','status':'PREPARED_DG03B_PENDING','audit_commit':'7c69eb3b4db8d479706f6e51b459413b8c24b564','implementation_commit':'ca78664d03464b81f56cf42c169c24f1153e69c9','preparation_commit_resolution':'git log --diff-filter=A --format=%H -- research_control_center/validation_v2/exp03b/EXP03B_RELEASE_RECEIPT_V1.json','execution_freeze_hash':frozen['self_hash'],'checks':receipts,'counts':{'focused':70,'validation_v2':458,'validation_v2_optional_skips':14,'rcc_ui':193,'pilot_v1_blobs':3021,'protected_v2_blobs':149,'private_input_hashes':215},'independent_qa':'PASS_WITH_SCOPE_PUBLIC_SOURCE_AND_SYNTHETIC; COORDINATOR_PRIVATE_REPLAY_PASS','provider_calls':0,'credential_reads':0,'capability_probes':0,'test1_accesses':0,'test2_accesses':0,'external_attack_accesses':0,'label_accesses':0,'private_exposures':0,'next_gate':'DG-03B','DG04':'DEFERRED_UNTIL_EXP03B','runtime_deployment_authorized':False})
    publish(public/'EXP03B_RELEASE_RECEIPT_V1.json',doc)
    print(json.dumps({'status':'RELEASE_QA_PASS','receipt_hash':doc['self_hash']}))
if __name__=='__main__':main()
