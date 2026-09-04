"""External custody adapter; frozen EXP01C training and EXP03B global equations."""
from .exp03b_contract_v1 import require, digest, SOURCES
from .gdn_corr_contract_v1 import Exp01CConfigV1
from .gdn_corr_v1 import purged_contiguous_validation_plan_v1
from .exp01c_backend_v1 import (_model_type_v1, _set_determinism, _edge_index, _window_batch,
    _embedding_scores_v1, _state_hash_v1, transform_with_frozen_scaler_v1, _all_edges,
    _graph_from_indices, train_exp01c_seed_v1)
from .exp01b_backend_v1 import aggregate_attention_from_augmented_tensors_v2
from .exp01b_functional_v1 import relative_delta_mse_v1
from .xver_gdn_roles_v1 import AuxiliaryEventEvidenceV1, event_validation_starts


def validate_checkpoint(*, checkpoint, identity, matrix, feature_order, pairs):
    import numpy as np
    require(checkpoint['run_identity']==identity,'RUN_IDENTITY')
    require(identity['version'] in ('22.04','21.03') and identity['split'] in ('train1','train2'),'RUN_SCOPE')
    require(identity['config_hash']==Exp01CConfigV1().config_hash==checkpoint['config_hash'],'CONFIG_IDENTITY')
    require(identity['device']=='cuda' and identity['dtype']=='float32','BACKEND_IDENTITY')
    require(identity['scaler_policy']=='TRAIN_ONLY_ROBUST_MEDIAN_IQR','SCALER_POLICY')
    require(identity['seed']==checkpoint['seed'] and checkpoint['view']==identity['split'].upper()+'_ONLY','SEED_VIEW_IDENTITY')
    require(type(feature_order) is tuple and len(feature_order)==len(set(feature_order))
            and digest(feature_order)==identity['feature_order_hash'],'NODE_ORDER_IDENTITY')
    require(matrix.shape==(identity['row_count'],len(feature_order)) and np.isfinite(matrix).all(),'NORMAL_MATRIX')
    require(len(pairs)==len(set(pairs)) and all(s!=t and s in feature_order and t in feature_order for s,t in pairs),'PAIR_CONTEXT')
    require(_state_hash_v1(checkpoint['state_dict'])==checkpoint['state_hash'],'CHECKPOINT_STATE')
    graph=tuple(tuple(e) for e in checkpoint['graph_edges'])
    from paperworks.v6.common import stable_hash_v1
    require(stable_hash_v1({'graph_edges':graph})==checkpoint['graph_hash'],'GRAPH_HASH')
    require(len(graph)==len(set(graph))==len(feature_order)*Exp01CConfigV1().learned_graph_topk
            and all(s!=t and s in feature_order and t in feature_order for s,t in graph),'GRAPH_CONTEXT')
    require(np.shape(checkpoint['scaler_center'])==np.shape(checkpoint['scaler_scale'])==(len(feature_order),),'SCALER_SHAPE')
    require(np.isfinite(checkpoint['scaler_center']).all() and np.isfinite(checkpoint['scaler_scale']).all()
            and (checkpoint['scaler_scale']>0).all(),'SCALER_FINITE')
    require(digest({'center':checkpoint['scaler_center'].tolist(),'scale':checkpoint['scaler_scale'].tolist()})==checkpoint['scaler_values_hash'],'SCALER_VALUES_HASH')
    config=Exp01CConfigV1()
    plan=purged_contiguous_validation_plan_v1(segment_lengths=(len(matrix),),seed=identity['seed'],history=5,max_horizon=62,validation_ratio=.2)
    require(tuple(checkpoint['validation_blocks'])==plan.validation_blocks and checkpoint['validation_window_count']==len(plan.validation_window_indices)
            and checkpoint['train_window_count']==len(plan.train_window_indices) and plan.raw_timestamp_overlap_count==0,'PURGED_PLAN')
    torch,_,kind=_model_type_v1(config);model=kind(len(feature_order)).to('cuda')
    model.load_state_dict(checkpoint['state_dict'],strict=True);model.eval()
    values=transform_with_frozen_scaler_v1((matrix,),center=checkpoint['scaler_center'],scale=checkpoint['scaler_scale'])[0]
    with torch.no_grad():
        start=plan.train_window_indices[0][1]
        x=torch.as_tensor(values[start:start+5].T[None],device='cuda')
        model(x,_all_edges(torch,len(feature_order),'cuda'))
    require(_graph_from_indices(feature_order,model.learned_graph)==graph,'GRAPH_STATE_REPLAY')
    return plan


def infer_global(*, identity, checkpoint, matrix, feature_order, pairs, progress=None):
    validate_checkpoint(checkpoint=checkpoint,identity=identity,matrix=matrix,feature_order=feature_order,pairs=pairs)
    return _global_core(split=identity['split'],checkpoint=checkpoint,matrix=matrix,feature_order=feature_order,pairs=pairs,progress=progress)


def _global_core(*, split: str, checkpoint: dict, matrix, feature_order: tuple, pairs: tuple, progress=None) -> dict:
    """Sequential reference masking, identical batch32 census; no refill or resampling."""
    require(split in ("train1","train2"),"BLOCKED_REQUIRED_SPLIT_PURE_GDN_EVIDENCE_CUSTODY")
    config=Exp01CConfigV1();view=split.upper()+"_ONLY"
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


def auxiliary_events(*, identity, checkpoint, matrix, feature_order, pairs, sources):
    """Isolated analysis-only sidecar: SCI01 events and fixed same-seed support."""
    from .exp02_bindings_v2a import extract_candidate_specific_events_v1
    from .exp03b_numeric_v1 import nearest
    from paperworks.v6.continuous_step_protocol_v1 import derive_source_screening_parameters_v1
    require(identity['split'] in ('train1','train2') and set(sources)<=set(feature_order),'AUX_SPLIT_SOURCES')
    require(digest(tuple(sources))==identity['source_universe_hash'],'AUX_SOURCE_UNIVERSE')
    plan=validate_checkpoint(checkpoint=checkpoint,identity=identity,matrix=matrix,feature_order=feature_order,pairs=pairs)
    positions={n:i for i,n in enumerate(feature_order)};events={}
    for source in sources:
        values=matrix[:,positions[source]]
        p=derive_source_screening_parameters_v1(tuple(map(float,values)))
        events[source]=() if p.source_step_threshold is None else extract_candidate_specific_events_v1(values,threshold=p.source_step_threshold,tolerance=p.source_stability_tolerance)
    config=Exp01CConfigV1();torch,_,kind=_model_type_v1(config);_set_determinism(torch,identity['seed'])
    model=kind(len(feature_order)).to('cuda');model.load_state_dict(checkpoint['state_dict'],strict=True);model.eval()
    values=torch.as_tensor(transform_with_frozen_scaler_v1((matrix,),center=checkpoint['scaler_center'],scale=checkpoint['scaler_scale'])[0],device='cuda')
    graph=tuple(tuple(e) for e in checkpoint['graph_edges']);edge=_edge_index(torch,feature_order,graph,device='cuda')
    output=[]
    for source,target in pairs:
        others=tuple(sorted({e.event_index for s,es in events.items() if s!=source for e in es}));rows=[]
        for direction in SOURCES:
            event_rows=tuple(e.event_index for e in events[source] if e.direction==direction and (nearest(e.event_index,others) is None or nearest(e.event_index,others)>2))
            starts=event_validation_starts(source_event_rows=event_rows,validation_indices=plan.validation_window_indices)
            state='NOT_IN_LEARNED_GRAPH' if (source,target) not in graph else 'NO_VALIDATION_EVENT' if not starts else 'AVAILABLE'
            baseline=torch.zeros(5,dtype=torch.float64);masked=torch.zeros(5,dtype=torch.float64)
            if state=='AVAILABLE':
                variant=_edge_index(torch,feature_order,tuple(e for e in graph if e!=(source,target)),device='cuda')
                indices=torch.tensor(starts,dtype=torch.long,device='cuda')
                with torch.no_grad():
                    for offset in range(0,len(starts),config.batch_size):
                        x,y=_window_batch(torch=torch,matrix=values,starts=indices[offset:offset+config.batch_size],config=config)
                        a=model.predict_fixed(x,edge);b=model.predict_fixed(x,variant);j=positions[target]
                        baseline+=((a[:,j,:]-y[:,j,:])**2).sum(dim=0).double().cpu()
                        masked+=((b[:,j,:]-y[:,j,:])**2).sum(dim=0).double().cpu()
            for j,h in enumerate(config.horizons):
                delta=None if state!='AVAILABLE' else relative_delta_mse_v1(baseline_target_mse=float(baseline[j]/len(starts)),masked_target_mse=float(masked[j]/len(starts)))
                rows.append((direction,h,len(starts),delta,state))
        output.append(AuxiliaryEventEvidenceV1(identity['version'],identity['split'],identity['seed'],source,target,tuple(rows)))
    require(_state_hash_v1(model.state_dict())==checkpoint['state_hash'],'AUX_CHECKPOINT_UNCHANGED')
    return tuple(output)
