"""Synthetic only: unchanged EXP01C equations with schema-sized fresh models."""
import json
import os
import platform
import time
from pathlib import Path
from hashlib import sha256
import numpy as np
from paperworks.validation_v2.exp01c_backend_v1 import (
    _model_type_v1, _set_determinism, _all_edges, _window_batch,
    _MultiHorizonDataset, _predict_variant_graphs_v1, _training_row_mask,
)
from paperworks.validation_v2.gdn_corr_contract_v1 import Exp01CConfigV1
from paperworks.validation_v2.gdn_corr_v1 import purged_contiguous_validation_plan_v1
from paperworks.validation_v2.exp03b_custody_v1 import replay, seal, publish
from paperworks.validation_v2.exp03b_contract_v1 import require

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'research_control_center/validation_v2/xver_normal'


def main() -> None:
    config=Exp01CConfigV1()
    torch,_,model_type=_model_type_v1(config)
    require(torch.cuda.is_available(),'CUDA_UNAVAILABLE')
    require(torch.cuda.get_device_name(0)=='NVIDIA GeForce RTX 5060 Laptop GPU','GPU_IDENTITY')
    _set_determinism(torch,11)
    records=[]
    for version in ('22','21'):
        doc=json.loads((PUBLIC/f'HAI{version}_GDN_CONTEXT_MAPPING_V1.json').read_text());replay(doc)
        count=len(doc['context_order']); torch.cuda.reset_peak_memory_stats()
        start=time.perf_counter()
        model=model_type(count).to(config.device)
        data=torch.randn((2,count,5),device=config.device)
        graph=_all_edges(torch,count,config.device)
        model.train();prediction=model(data,graph)
        require(tuple(prediction.shape)==(2,count,5),'OUTPUT_SHAPE')
        loss=prediction.square().mean();loss.backward()
        neighbors=model.learned_graph
        require(not bool((neighbors==torch.arange(count,device='cuda')[:,None]).any()),'SELF_EXCLUSION')
        model.eval()
        with torch.no_grad():
            a=model.predict_fixed(data,graph);b=model.predict_fixed(data,graph)
            require(torch.equal(a,b),'ATTENTION_INVARIANCE')
            graphs=(graph,graph[:,1:])
            variants=_predict_variant_graphs_v1(torch=torch,model=model,data=data,graphs=graphs,node_count=count)
            reference=torch.stack([model.predict_fixed(data,g) for g in graphs])
            require(bool(torch.allclose(variants,reference,atol=1e-7,rtol=1e-6)),'MASK_BATCH_EQUIVALENCE')
            values=np.random.default_rng(11).normal(size=(300,count)).astype(np.float32)
            plan=purged_contiguous_validation_plan_v1(segment_lengths=(300,),seed=11,history=5,max_horizon=62,validation_ratio=.2)
            require(plan.raw_timestamp_overlap_count==0,'PURGE_OVERLAP')
            ds=_MultiHorizonDataset((values,),plan.train_window_indices,config=config,torch_module=torch)
            starts=torch.tensor([i for f,i in plan.train_window_indices[:2]],device='cuda')
            x,y=_window_batch(torch=torch,matrix=torch.tensor(values,device='cuda'),starts=starts,config=config)
            for i in range(2):
                rx,ry,_,_=ds[i]
                require(torch.equal(x[i].cpu(),rx) and torch.equal(y[i].cpu(),ry),'WINDOW_EQUIVALENCE')
        torch.cuda.synchronize()
        records.append({'version':version,'node_count':count,'output_shape':list(prediction.shape),
            'embedding_shape':list(model.embedding.weight.shape),'self_exclusion':True,
            'fresh_weights':True,'attention_invariance':True,'edge_mask_batch_equivalence':True,
            'window_equivalence':True,'raw_timestamp_overlap':0,
            'wall_seconds':time.perf_counter()-start,'peak_allocated_VRAM_bytes':torch.cuda.max_memory_allocated(),
            'scope':'SYNTHETIC_FORWARD_BACKWARD_ONLY_NOT_SCIENTIFIC_TRAINING'})
        del model,data,prediction,variants,reference
    result=seal({'schema':'xver_variable_node_synthetic_receipt_v1','status':'PASS',
        'records':records,'python':platform.python_version(),'torch':torch.__version__,
        'cuda_build':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'dtype':'float32',
        'config_hash':config.config_hash,'cublas_workspace_config':os.environ.get('CUBLAS_WORKSPACE_CONFIG'),
        'synthetic_seed':11,'scientific_runs':0,'weights_transferred':False,
        'implementation_hash':sha256(Path(__file__).read_bytes()).hexdigest(),
        'provider_calls':0,'credential_reads':0,'attack_data_accesses':0})
    publish(PUBLIC/'GDN_VARIABLE_NODE_SYNTHETIC_RECEIPT_V1.json',result)
    print(json.dumps({'status':'PASS','node_counts':[r['node_count'] for r in records],
                      'scientific_runs':0,'receipt_hash':result['self_hash']}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'SYNTHETIC_PREFLIGHT_FAILED','error_type':type(error).__name__,
            'code':str(error) if isinstance(error,ValueError) and str(error).replace('_','').isalnum() else 'REDACTED'}))
        raise SystemExit(2)
