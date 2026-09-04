"""Fixed-checkpoint, split-pure validation inference. No training or file I/O."""
from .exp03b_contract_v1 import require
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER
from .gdn_corr_contract_v1 import Exp01CConfigV1
from .gdn_corr_v1 import purged_contiguous_validation_plan_v1
from .exp01c_backend_v1 import (_model_type_v1, _set_determinism, _edge_index, _window_batch, _embedding_scores_v1, _state_hash_v1, transform_with_frozen_scaler_v1)
from .exp01b_backend_v1 import aggregate_attention_from_augmented_tensors_v2
from .exp01b_functional_v1 import relative_delta_mse_v1


def infer(*, split: str, checkpoint: dict, matrix, feature_order: tuple, pairs: tuple, progress=None) -> dict:
    """Sequential reference masking, identical batch32 census; no refill or resampling."""
    require(split in ("train1","train2"),"BLOCKED_REQUIRED_SPLIT_PURE_GDN_EVIDENCE_CUSTODY")
    config=Exp01CConfigV1();view=split.upper()+"_ONLY"
    require(feature_order==tuple(P1_FEATURE_ORDER),"GDN_FEATURE_ORDER")
    require(len(matrix)==(280800 if split=="train1" else 291600),"GDN_SPLIT_LENGTH_AUTHORITY")
    require(checkpoint["view"]==view and checkpoint["config_hash"]==config.config_hash,"GDN_SPLIT_OR_CONFIG")
    seed=checkpoint["seed"]
    require(seed in (11,23,37),"GDN_SEED")
    plan=purged_contiguous_validation_plan_v1(segment_lengths=(len(matrix),),seed=seed,history=5,max_horizon=62,validation_ratio=.2)
    require(tuple(checkpoint["validation_blocks"])==plan.validation_blocks and checkpoint["validation_window_count"]==len(plan.validation_window_indices) and plan.raw_timestamp_overlap_count==0,"GDN_PURGED_PARTITION")
    torch,_,model_type=_model_type_v1(config);_set_determinism(torch,seed)
    require(torch.cuda.is_available() and config.device=="cuda","FROZEN_CUDA_REQUIRED")
    model=model_type(len(feature_order)).to(config.device);model.load_state_dict(checkpoint["state_dict"],strict=True);model.eval()
    before=_state_hash_v1(model.state_dict());require(before==checkpoint["state_hash"],"GDN_STATE")
    transformed=transform_with_frozen_scaler_v1((matrix,),center=checkpoint["scaler_center"],scale=checkpoint["scaler_scale"])[0]
    values=torch.as_tensor(transformed,dtype=torch.float32,device=config.device).contiguous()
    graph=tuple(tuple(e) for e in checkpoint["graph_edges"]);positions={x:i for i,x in enumerate(feature_order)}
    require(all(s!=t for s,t in graph),"GDN_SELF_EDGE")
    edge_index=_edge_index(torch,feature_order,graph,device=config.device)
    members=tuple(pair for pair in pairs if pair in graph)
    variants={p:_edge_index(torch,feature_order,tuple(e for e in graph if e!=p),device=config.device) for p in members}
    baseline_sum=torch.zeros((len(feature_order),5),dtype=torch.float64)
    masked_sum={p:torch.zeros(5,dtype=torch.float64) for p in members}
    attention_sum={p:0. for p in members};count=len(plan.validation_window_indices)
    starts=torch.tensor([i for f,i in plan.validation_window_indices if f==0],dtype=torch.long,device=config.device)
    require(len(starts)==count and count>0,"GDN_FILE_LOCAL")
    with torch.no_grad():
        for offset in range(0,count,config.batch_size):
            x,y=_window_batch(torch=torch,matrix=values,starts=starts[offset:offset+config.batch_size],config=config)
            baseline=model.predict_fixed(x,edge_index);captured=model.predict_fixed(x,edge_index)
            require(bool(torch.allclose(baseline,captured,atol=1e-7,rtol=1e-6)),"ATTENTION_INVARIANCE")
            alpha=model.gnn_layer.gnn._alpha
            from torch_geometric.utils import add_self_loops, remove_self_loops
            augmented,_=remove_self_loops(model._batch_edges(edge_index,len(x),len(feature_order)))
            augmented,_=add_self_loops(augmented,num_nodes=len(x)*len(feature_order))
            mapped=aggregate_attention_from_augmented_tensors_v2(torch_module=torch,augmented_edges=augmented,alpha_values=alpha,node_count=len(feature_order),feature_order=feature_order,graph_edges=graph,batch_size=len(x))
            for pair in members:attention_sum[pair]+=mapped[pair]*len(x)
            baseline_sum+=((baseline-y)**2).sum(dim=0).double().cpu()
            for pair in members:
                predicted=model.predict_fixed(x,variants[pair]);j=positions[pair[1]]
                masked_sum[pair]+=((predicted[:,j,:]-y[:,j,:])**2).sum(dim=0).double().cpu()
            if progress and offset%(config.batch_size*200)==0:progress(min(offset+len(x),count),count)
    require(before==_state_hash_v1(model.state_dict()),"CHECKPOINT_MUTATED")
    embedding=_embedding_scores_v1(torch=torch,model=model,order=feature_order,pairs=pairs)
    rows=[]
    for pair in pairs:
        for j,h in enumerate(config.horizons):
            delta=None
            if pair in members:delta=relative_delta_mse_v1(baseline_target_mse=float(baseline_sum[positions[pair[1]],j]/count),masked_target_mse=float(masked_sum[pair][j]/count))
            rows.append({"source":pair[0],"target":pair[1],"horizon":h,"embedding":embedding[pair],"attention":attention_sum[pair]/count if pair in members else 0.,"edge_delta":delta,"state":"DIRECT_FIXED_EDGE" if pair in members else "NOT_IN_LEARNED_GRAPH"})
    return {"split":split,"view":view,"seed":seed,"state_hash":before,"validation_window_count":count,"attention_scope":"SHARED_ENCODER_NOT_HEAD_SPECIFIC","rows":rows,"checkpoint_unchanged":True,"retrained":False}
