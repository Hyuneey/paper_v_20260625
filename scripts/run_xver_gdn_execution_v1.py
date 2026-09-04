"""Single-owner normal-only GDN runner. No provider/credential/attack capability."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import io
import json
import os
import platform
import subprocess
import threading
import time
import uuid
import numpy as np
from xver_execution_common import (ROOT,PUB,document,version_authorities,load_projection,
    private_root,committed,head,publish,replay,seal,require,digest,sha256_file)
from replay_xver_execution_inputs_v1 import replay_inputs
from paperworks.validation_v2.gdn_corr_contract_v1 import Exp01CConfigV1
from paperworks.validation_v2.exp01c_backend_v1 import (_model_type_v1,_set_determinism,_state_hash_v1,
    _MultiHorizonDataset,_window_batch,_fit_scaler_and_transform)
from paperworks.validation_v2.gdn_corr_v1 import purged_contiguous_validation_plan_v1
from paperworks.validation_v2.xver_gdn_execution_v1 import train_exp01c_seed_v1,infer_global,auxiliary_events,validate_checkpoint

CONTRACT=PUB/'GDN_EXECUTION_AUTHORITY_V1.json'
IMPLEMENTATION=('scripts/run_xver_gdn_execution_v1.py','scripts/xver_execution_common.py',
    'scripts/replay_xver_execution_inputs_v1.py','src/paperworks/validation_v2/xver_gdn_execution_v1.py',
    'src/paperworks/validation_v2/xver_gdn_roles_v1.py','src/paperworks/validation_v2/xver_gdn_provider_v1.py',
    'src/paperworks/validation_v2/exp01c_backend_v1.py','src/paperworks/validation_v2/gdn_corr_contract_v1.py',
    'src/paperworks/validation_v2/gdn_corr_v1.py','src/paperworks/validation_v2/exp03b_gdn_v1.py',
    'src/paperworks/validation_v2/exp01b_backend_v1.py','src/paperworks/validation_v2/exp01b_functional_v1.py',
    'src/paperworks/validation_v2/exp02_bindings_v2a.py','src/paperworks/v6/continuous_step_protocol_v1.py',
    'src/paperworks/validation_v2/exp03b_numeric_v1.py')


def environment():
    require(os.environ.get('CUBLAS_WORKSPACE_CONFIG')==':4096:8' and os.environ.get('PYTHONHASHSEED')=='0','DETERMINISM_ENVIRONMENT')
    config=Exp01CConfigV1();torch,_,_=_model_type_v1(config);_set_determinism(torch,11)
    require(torch.cuda.is_available() and torch.cuda.get_device_name(0)=='NVIDIA GeForce RTX 5060 Laptop GPU','FROZEN_GPU_REQUIRED')
    driver=subprocess.check_output(['nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],text=True).strip()
    return {'python':platform.python_version(),'OS':platform.platform(),'torch':torch.__version__,
        'CUDA_build':torch.version.cuda,'GPU':torch.cuda.get_device_name(0),'driver':driver,
        'dtype':config.dtype,'device':config.device,'deterministic_algorithms':torch.are_deterministic_algorithms_enabled(),
        'cudnn_deterministic':torch.backends.cudnn.deterministic,'cudnn_benchmark':torch.backends.cudnn.benchmark,
        'cublas_workspace_config':os.environ.get('CUBLAS_WORKSPACE_CONFIG'),'pythonhashseed':os.environ.get('PYTHONHASHSEED')}


def freeze():
    replay_inputs()
    hashes={p:sha256_file(ROOT/p) for p in IMPLEMENTATION}
    for path in IMPLEMENTATION:committed(ROOT/path)
    env=environment();config=Exp01CConfigV1();versions={}
    for version in ('22.04','21.03'):
        context,candidate,roles,pairs=version_authorities(version)
        projections=document(PUB/f'HAI{version[:2]}_GDN_CONTEXT_PROJECTION_RECEIPT_V1.json')
        versions[version]={'context_hash':context['self_hash'],'context_order':context['context_order'],
            'candidate_hash':candidate['self_hash'],'N':len(pairs),'source_universe':roles['sources'],
            'projection_bundle_hash':projections['self_hash']}
    value=seal({'schema':'xver_gdn_execution_authority_v1','status':'FROZEN_BEFORE_PREFLIGHT_AND_RUN1',
        'source_commit':head(),'implementation_hashes':hashes,'environment':env,'environment_hash':digest(env),
        'binding_hash':document(PUB/'GDN_SEPARATED_EVIDENCE_BINDING_V1.json')['self_hash'],
        'configuration':config.to_dict(),'configuration_hash':config.config_hash,'versions':versions,
        'schedule':[{'version':v,'split':s,'seed':seed} for v in versions for s in ('train1','train2') for seed in (11,23,37)],
        'scaler_policy':'TRAIN_ONLY_ROBUST_MEDIAN_IQR','purge':'UNCHANGED_EXP01C_HISTORY5_MAX_RESPONSE62_RATIO0.2',
        'preflight_rows':512,'preflight_seed':11,'preflight_training':'UNCHANGED_FULL_CONFIG_ON_BOUNDED_NORMAL_PREFIX',
        'preflight_aggregated':False,'scientific_GPU_owners':1,'provider_calls_authorized':False,
        'attack_access_authorized':False,'global_event_fusion':False,'trained_HAI23_weights':False})
    publish(CONTRACT,value);print(json.dumps({'status':'EXECUTION_AUTHORITY_FROZEN','hash':value['self_hash']}),flush=True)


def replay_execution():
    authority=document(CONTRACT);committed(CONTRACT)
    for path,h in authority['implementation_hashes'].items():
        require(sha256_file(ROOT/path)==h,'EXECUTION_CODE_CHANGED');committed(ROOT/path)
    require(environment()==authority['environment'],'EXECUTION_ENVIRONMENT_CHANGED')
    require(document(PUB/'GDN_SEPARATED_EVIDENCE_BINDING_V1.json')['self_hash']==authority['binding_hash'],'BINDING_CHANGED')
    return authority


def identity_for(authority,version,split,seed,matrix,order,receipt,scope):
    context,candidate,roles,pairs=version_authorities(version)
    bound=authority['versions'][version]
    require(bound['context_hash']==context['self_hash'] and bound['candidate_hash']==candidate['self_hash']
        and order==tuple(bound['context_order']) and bound['source_universe']==roles['sources'],'VERSION_AUTHORITY_CHANGED')
    identity={'version':version,'split':split,'view':split.upper()+'_ONLY','seed':seed,'scope':scope,
        'context_hash':context['self_hash'],'node_count':len(order),'feature_order_hash':digest(order),
        'source_universe_hash':digest(tuple(roles['sources'])),'projection_hash':receipt['projection_hash'],
        'row_count':len(matrix),'row_interval':[0,len(matrix)],'candidate_hash':candidate['self_hash'],
        'config_hash':authority['configuration_hash'],'source_commit':authority['source_commit'],
        'implementation_hash':digest(authority['implementation_hashes']),'authority_hash':authority['self_hash'],
        'device':'cuda','dtype':'float32','scaler_policy':authority['scaler_policy'],'purge_contract':authority['purge']}
    return identity,roles,pairs


def checkpoint_payload(trained,identity):
    data=asdict(trained)
    data.update(run_identity=identity,state_hash=_state_hash_v1(trained.state_dict),config_hash=identity['config_hash'],
        view=identity['view'],seed=identity['seed'],scaler_values_hash=digest({'center':trained.scaler_center.tolist(),'scale':trained.scaler_scale.tolist()}))
    return data


def persist_checkpoint(path,payload):
    import torch
    require(not path.exists() and not path.with_suffix('.partial').exists(),'CHECKPOINT_APPEND_ONLY')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.with_suffix('.partial').open('xb') as stream:
        torch.save(payload,stream);stream.flush();os.fsync(stream.fileno())
    os.rename(path.with_suffix('.partial'),path)
    h=sha256_file(path)
    restored=torch.load(path,map_location='cpu',weights_only=False)
    require(restored['run_identity']==payload['run_identity'] and _state_hash_v1(restored['state_dict'])==payload['state_hash'],'CHECKPOINT_DURABLE_REPLAY')
    return restored,h


class Monitor:
    def __init__(self):self.stop=threading.Event();self.samples=[]
    def start(self):
        def sample():
            while not self.stop.is_set():
                try:
                    output=subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True,creationflags=subprocess.CREATE_NO_WINDOW)
                    self.samples.append(tuple(float(x.strip()) for x in output.strip().split(',')))
                except (OSError,ValueError,subprocess.SubprocessError):pass
                self.stop.wait(1.)
        self.thread=threading.Thread(target=sample,daemon=True);self.thread.start()
    def finish(self):
        self.stop.set();self.thread.join(timeout=5)
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
        counters=Counters();counters.cb=ctypes.sizeof(counters)
        get=ctypes.windll.kernel32.GetCurrentProcess;get.restype=ctypes.c_void_p
        fn=ctypes.windll.psapi.GetProcessMemoryInfo;fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),wintypes.DWORD]
        ok=fn(get(),ctypes.byref(counters),ctypes.sizeof(counters))
        require(bool(ok) and bool(self.samples),'PREFLIGHT_TELEMETRY_REQUIRED')
        return {'peak_process_working_set_bytes':counters.PeakWorkingSetSize,'GPU_utilization_mean_percent':float(np.mean([x[0] for x in self.samples])),
                'GPU_utilization_max_percent':max(x[0] for x in self.samples),'sample_count':len(self.samples),'sample_period_seconds':1}


def run_one(version,split,seed,preflight=False):
    import torch
    authority=replay_execution()
    require({'version':version,'split':split,'seed':seed} in authority['schedule'],'RUN_SCHEDULE')
    if not preflight:
        pre=document(PUB/f'HAI{version[:2]}_GDN_PREFLIGHT_RECEIPT_V1.json')
        require(pre['status']=='PASS' and pre['authority_hash']==authority['self_hash'],'PREFLIGHT_REQUIRED')
    started=time.perf_counter();matrix,order,receipt=load_projection(version,split,context=True)
    if preflight:matrix=matrix[:authority['preflight_rows']].copy()
    scope='PREFLIGHT_ONLY' if preflight else 'SCIENTIFIC'
    identity,roles,pairs=identity_for(authority,version,split,seed,matrix,order,receipt,scope)
    directory=private_root()/('preflight' if preflight else 'runs')/digest(identity)
    directory.mkdir(parents=True,exist_ok=True)
    publish(directory/'identity.json',seal(identity))
    public_result=PUB/f'HAI{version[:2]}_GDN_PREFLIGHT_RECEIPT_V1.json' if preflight else PUB/'runs'/f'HAI{version[:2]}_{split.upper()}_SEED{seed}_RECEIPT_V1.json'
    if public_result.exists():
        result=document(public_result)
        require(result['run_identity_hash']==digest(identity) and result['authority_hash']==authority['self_hash'],'COMPLETED_RUN_IDENTITY')
        for name,key in [('checkpoint.pt','checkpoint_sha256'),('global.json','global_hash'),('auxiliary_event.json','auxiliary_hash')]:
            require(sha256_file(directory/name)==result[key],'COMPLETED_RUN_BYTES')
        print(json.dumps({'status':'EXACT_COMPLETED_RUN_REPLAY_NO_TRAINING','version':version,'split':split,'seed':seed}),flush=True)
        return
    lock_path=private_root()/'GPU_OWNER.lock'
    # Exclusive process ownership; a crash leaves explicit custody evidence for repair, never auto-delete.
    with lock_path.open('x') as lock:
        lock.write(json.dumps({'pid':os.getpid(),'identity_hash':digest(identity)}));lock.flush();os.fsync(lock.fileno())
    attempt=uuid.uuid4().hex
    publish(directory/f'attempt_{attempt}_started.json',seal({'identity_hash':digest(identity),'state':'STARTED','source_commit':head()}))
    monitor=Monitor();monitor.start();torch.cuda.reset_peak_memory_stats()
    try:
        path=directory/'checkpoint.pt'
        if path.exists():
            cr=document(directory/'checkpoint_receipt.json');require(sha256_file(path)==cr['sha256'],'CHECKPOINT_BYTES')
            checkpoint=torch.load(path,map_location='cpu',weights_only=False)
        else:
            print(json.dumps({'phase':'PREFLIGHT_TRAIN' if preflight else 'SCIENTIFIC_TRAIN','version':version,'split':split,'seed':seed,'run_id':digest(identity)}),flush=True)
            trained=train_exp01c_seed_v1(segments=(matrix,),feature_order=order,seed=seed,preprocessing_policy=authority['scaler_policy'],config=Exp01CConfigV1())
            payload=checkpoint_payload(trained,identity);serial=time.perf_counter()
            checkpoint,ch=persist_checkpoint(path,payload)
            publish(directory/'checkpoint_receipt.json',seal({'sha256':ch,'identity_hash':digest(identity),'state_hash':payload['state_hash'],
                'serialization_seconds':time.perf_counter()-serial}))
            del trained,payload
        plan=validate_checkpoint(checkpoint=checkpoint,identity=identity,matrix=matrix,feature_order=order,pairs=pairs)
        transformed,_,_,_=_fit_scaler_and_transform((matrix,),train_indices=plan.train_window_indices,policy=authority['scaler_policy'],config=Exp01CConfigV1())
        ds=_MultiHorizonDataset(transformed,plan.train_window_indices,config=Exp01CConfigV1(),torch_module=torch)
        starts=torch.tensor([i for _,i in plan.train_window_indices[:2]],device='cuda')
        x,y=_window_batch(torch=torch,matrix=torch.tensor(transformed[0],device='cuda'),starts=starts,config=Exp01CConfigV1())
        for i in range(2):
            rx,ry,_,_=ds[i];require(torch.equal(x[i].cpu(),rx) and torch.equal(y[i].cpu(),ry),'WINDOW_REFERENCE_EQUIVALENCE')
        del transformed,ds,x,y
        gp=directory/'global.json'
        if gp.exists():
            global_result=document(gp)
            require(global_result['split']==split and global_result['seed']==seed and global_result['state_hash']==checkpoint['state_hash'],'GLOBAL_CACHE_IDENTITY')
        else:
            global_result=seal(infer_global(identity=identity,checkpoint=checkpoint,matrix=matrix,feature_order=order,pairs=pairs,
                progress=lambda n,total:print(json.dumps({'phase':'GLOBAL','version':version,'split':split,'seed':seed,'windows':n,'total':total}),flush=True)))
            publish(gp,global_result)
        global_hash=sha256_file(gp)
        require(len(global_result['rows'])==5*len(pairs),'GLOBAL_ROW_CENSUS')
        require(all(np.isfinite(r['embedding']) and np.isfinite(r['attention']) and (r['edge_delta'] is None or np.isfinite(r['edge_delta'])) for r in global_result['rows']),'GLOBAL_FINITE')
        auxiliary=auxiliary_events(identity=identity,checkpoint=checkpoint,matrix=matrix,feature_order=order,pairs=pairs,sources=tuple(roles['sources']))
        publish(directory/'auxiliary_event.json',seal({'purpose':'AUXILIARY_CORROBORATION_ONLY','identity_hash':digest(identity),'rows':[asdict(r) for r in auxiliary]}))
        require(sha256_file(gp)==global_hash,'AUX_GLOBAL_NONINTERFERENCE')
        telemetry=monitor.finish();elapsed=time.perf_counter()-started
        states={}
        for item in auxiliary:
            for row in item.rows:states[row[4]]=states.get(row[4],0)+1
        result=seal({'schema':'xver_gdn_run_receipt_v1','status':'PASS','scope':scope,'version':version,'split':split,'seed':seed,
            'authority_hash':authority['self_hash'],'run_identity_hash':digest(identity),'node_count':len(order),
            'checkpoint_sha256':sha256_file(path),'state_hash':checkpoint['state_hash'],'global_hash':global_hash,
            'auxiliary_hash':sha256_file(directory/'auxiliary_event.json'),'candidate_count':len(pairs),
            'global_row_count':len(global_result['rows']),'auxiliary_row_count':10*len(auxiliary),'auxiliary_states':states,
            'completed_epochs':checkpoint['completed_epochs'],'train_window_count':checkpoint['train_window_count'],
            'validation_window_count':checkpoint['validation_window_count'],'raw_timestamp_overlap':0,
            'wall_seconds':elapsed,'training_window_visits_per_wall_second':checkpoint['train_window_count']*checkpoint['completed_epochs']/elapsed,
            'peak_allocated_VRAM_bytes':torch.cuda.max_memory_allocated(),'telemetry':telemetry,
            'serialization_seconds':document(directory/'checkpoint_receipt.json')['serialization_seconds'],
            'window_reference_equivalence':True,'global_kernel_AST_equivalence':True,'global_auxiliary_fused':False,
            'provider_calls':0,'credential_reads':0,'attack_accesses':0,'excluded_label_values_parsed':False})
        publish(directory/f'attempt_{attempt}_complete.json',result)
        if preflight:publish(PUB/f'HAI{version[:2]}_GDN_PREFLIGHT_RECEIPT_V1.json',result)
        else:publish(PUB/'runs'/f'HAI{version[:2]}_{split.upper()}_SEED{seed}_RECEIPT_V1.json',result)
        print(json.dumps({'phase':scope,'status':'PASS','version':version,'split':split,'seed':seed,'wall_seconds':elapsed}),flush=True)
    except Exception as error:
        publish(directory/f'attempt_{attempt}_failed.json',seal({'status':'FAILED','identity_hash':digest(identity),'error_type':type(error).__name__,
            'code':str(error) if type(error) is ValueError and str(error).replace('_','').isalnum() else 'REDACTED'}))
        raise
    finally:
        monitor.stop.set();monitor.thread.join(timeout=5)
        lock_path.unlink()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('freeze','preflight','run'));parser.add_argument('--version',choices=('22.04','21.03'));parser.add_argument('--split',choices=('train1','train2'));parser.add_argument('--seed',type=int,choices=(11,23,37));args=parser.parse_args()
    try:
        if args.phase=='freeze':freeze()
        elif args.phase=='preflight':run_one(args.version,'train1',11,True)
        else:run_one(args.version,args.split,args.seed)
    except Exception as error:
        print(json.dumps({'status':'BLOCKED_EXECUTION_ADAPTER','error_type':type(error).__name__,
            'code':str(error) if type(error) is ValueError and str(error).replace('_','').isalnum() else 'REDACTED'}),flush=True);raise SystemExit(2)
