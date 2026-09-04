"""External normal-only evidence/T0 closure. No transport, credentials or raw CSV."""
import argparse
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
import json
import time
import numpy as np
from xver_execution_common import ROOT, PUB, PARENT, private_root, document, version_authorities, load_projection, committed, head, publish, seal, require, digest, sha256_file
from paperworks.validation_v2.xver_structural_v1 import build_structural
from paperworks.validation_v2.xver_confirmation_v1 import fit_and_confirm_mapped_union_v1
from paperworks.validation_v2.xver_numeric_closure_v1 import authorize_t0_binding, bind_t0_rule
from paperworks.validation_v2.exp03b_contract_v1 import StructuralTupleEvidenceV1, SemanticTupleV1
from paperworks.validation_v2.exp03b_semantic_v2 import Train1SemanticEvidenceV2, t0, proposal_document, parse_proposal
from paperworks.validation_v2.exp03b_hidden_v2 import Train2SemanticEvidenceV2, Train2HiddenVerifierAuthorityV2, verify
from paperworks.validation_v2.exp03b_execution_v2 import admit
from paperworks.validation_v2.exp03b_binder_v2 import POLICY
from paperworks.validation_v2.exp03b_numeric_v1 import summarize_column, census
from paperworks.validation_v2.exp03b_evaluation import run_guard_portfolio
from paperworks.validation_v2.exp03b_guard_v1 import Train4HiddenGuardAuthorityV1, portfolio_census
from paperworks.validation_v2.exp03b_conversion import convert
from paperworks.validation_v2.exp03b_metrics_v1 import strict_metrics
from paperworks.validation_v2.exp02_bindings_v2a import extract_candidate_specific_events_v1
from paperworks.validation_v2.xver_gdn_roles_v1 import GlobalSeedEvidenceV1, retrieval_global
from paperworks.validation_v2.xver_gdn_provider_v1 import project_global_only
from paperworks.candidates.statistical_candidate_discovery_v1 import vectorized_file_lagged_correlations_v1

CONTRACT = PUB/'SEMANTIC_EXECUTION_AUTHORITY_V1.json'
MODULES = ('xver_structural_v1','xver_confirmation_v1','xver_numeric_closure_v1','exp03b_semantic_v2','exp03b_hidden_v2','exp03b_execution_v2','exp03b_binder_v2','exp03b_numeric_v1','exp03b_evaluation','exp03b_guard_v1','exp03b_conversion','exp03b_metrics_v1','exp03b_contract_v1','exp03b_evidence_v1','exp03b_custody_v1','exp03b_firewall_v1','exp03b_firewall_v2','xver_gdn_roles_v1','xver_gdn_provider_v1','exp02_bindings_v2a','exp01_relation_confirmation_v2','formal_v4_authority_v1','runtime_v1','numeric_policy_v1')
IMPLEMENTATION = ('scripts/run_xver_semantic_execution_v1.py','scripts/xver_execution_common.py') + tuple('src/paperworks/validation_v2/'+n+'.py' for n in MODULES) + ('src/paperworks/v6/relation_profiling_protocol_v1.py','src/paperworks/v6/continuous_step_protocol_v1.py','src/paperworks/profiling/task039d1_execution_optimization_v1.py','src/paperworks/candidates/statistical_candidate_discovery_v1.py')


def safe(value):
    if isinstance(value,Fraction):return {'numerator':value.numerator,'denominator':value.denominator}
    if isinstance(value,dict):return {k:safe(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [safe(v) for v in value]
    return value


def freeze():
    hashes={p:sha256_file(ROOT/p) for p in IMPLEMENTATION}
    for p in IMPLEMENTATION:committed(ROOT/p)
    versions={}
    for v in ('22.04','21.03'):
        context,candidate,roles,pairs=version_authorities(v)
        versions[v]={'candidate_hash':candidate['self_hash'],'role_hash':roles['self_hash'],'projection_hash':document(PARENT/f'HAI{v[:2]}_NORMAL_PROJECTION_RECEIPT_V2.json')['self_hash'],'N':len(pairs)}
    authority=seal({'schema':'xver_semantic_execution_authority_v1','source_commit':head(),'implementation_hashes':hashes,'versions':versions,'GDN_execution_hash':document(PUB/'GDN_EXECUTION_AUTHORITY_V2.json')['self_hash'],'T0':'EXACT_EXP03B_SEMANTIC_V2_ONCE_STRUCTURAL_ONLY','confirmation':'EXACT_EXP01_ARM_BLIND_FIT_TRAIN1_TRAIN2_CONFIRM_TRAIN3_SCHEMA_INTERSECTION','numeric_policy':POLICY,'HAI21_train3_intervals':{'confirmation':[0,239370],'purge':[239370,239430],'guard':[239430,478801]},'auxiliary_consumption':False,'provider_calls_authorized':False,'attack_access_authorized':False})
    publish(CONTRACT,authority);print(json.dumps({'status':'SEMANTIC_AUTHORITY_FROZEN','hash':authority['self_hash']}),flush=True)


def replay_authority(version):
    a=document(CONTRACT);committed(CONTRACT)
    for p,h in a['implementation_hashes'].items():require(sha256_file(ROOT/p)==h,'SEMANTIC_SOURCE_CHANGED');committed(ROOT/p)
    c,ca,r,p=version_authorities(version);v=a['versions'][version]
    require((ca['self_hash'],r['self_hash'])==(v['candidate_hash'],v['role_hash']),'SEMANTIC_COHORT_CHANGED')
    require(document(PARENT/f'HAI{version[:2]}_NORMAL_PROJECTION_RECEIPT_V2.json')['self_hash']==v['projection_hash'],'NORMAL_PROJECTION_CHANGED')
    require(document(PUB/'GDN_EXECUTION_AUTHORITY_V2.json')['self_hash']==a['GDN_execution_hash'],'FROZEN_GDN_EXECUTION_CHANGED')
    return a,c,ca,r,p


def run_directory(version):return private_root()/'semantic'/('HAI'+version[:2])


def global_seeds(version,split,pairs):
    """Only GLOBAL files are opened; auxiliary has no read path in this module."""
    result={p:[] for p in pairs};hashes=[]
    for seed in (11,23,37):
        r=document(PUB/'runs'/f'HAI{version[:2]}_{split.upper()}_SEED{seed}_RECEIPT_V1.json')
        require(r['scope']=='SCIENTIFIC' and r['status']=='PASS' and (r['version'],r['split'],r['seed'])==(version,split,seed),'GLOBAL_RUN_IDENTITY')
        require(r['authority_hash']==document(PUB/'GDN_EXECUTION_AUTHORITY_V2.json')['self_hash'],'GLOBAL_EXECUTION_BINDING')
        p=private_root()/'runs'/r['run_identity_hash']/'global.json'
        require(sha256_file(p)==r['global_hash'],'GLOBAL_BYTES');g=document(p);hashes.append(r['self_hash'])
        require(g['split']==split and g['seed']==seed and g['state_hash']==r['state_hash'],'GLOBAL_CONTENT_IDENTITY')
        for pair in pairs:
            rows=sorted((x for x in g['rows'] if (x['source'],x['target'])==pair),key=lambda x:x['horizon'])
            result[pair].append(GlobalSeedEvidenceV1(version,split,seed,*pair,tuple((x['horizon'],x['embedding'],x['attention'],x['edge_delta']) for x in rows)))
    return {p:tuple(s) for p,s in result.items()},digest(hashes)


def hydrate(value):
    rows=tuple(StructuralTupleEvidenceV1(SemanticTupleV1(**r['semantic']),**{k:v for k,v in r.items() if k!='semantic'}) for r in value['rows'])
    cls=Train1SemanticEvidenceV2 if value['split']=='train1' else Train2SemanticEvidenceV2
    return cls(value['candidate_id'],value['source'],value['target'],value['input_hash'],rows)


def evidence(version):
    a,context,candidate,roles,pairs=replay_authority(version);directory=run_directory(version)
    records=[]
    for split in ('train1','train2'):
        seeds,gh=global_seeds(version,split,pairs)
        matrix,order,receipt=load_projection(version,split)
        bundles=build_structural(split=split,matrix=matrix,feature_order=order,pairs=pairs,all_sources=tuple(roles['sources']),all_targets=tuple(roles['targets']),input_hash=receipt['projection_hash'])
        positions={s:i for i,s in enumerate(order)}
        source=tuple(roles['sources']);target=tuple(roles['targets'])
        stat=vectorized_file_lagged_correlations_v1(source_values=matrix[:,[positions[s] for s in source]],target_values=matrix[:,[positions[t] for t in target]])
        for b in bundles:
            pair=(b.source,b.target)
            observed=[abs(float(m[source.index(pair[0]),target.index(pair[1])])) for m in stat.values() if np.isfinite(m[source.index(pair[0]),target.index(pair[1])])]
            association=max(observed) if observed else 0.0
            sh=publish(directory/split/'structural'/f'{b.candidate_id}.json',seal(asdict(b)))
            if split=='train1':
                pack=project_global_only(version=version,train1=b,global_seeds=seeds[pair],stat_association=association,checkpoint_receipt_hash=gh)
                ph=publish(directory/'provider'/f'{b.candidate_id}.json',pack)
            else:
                rows=retrieval_global(seeds[pair],version=version)
                pack={'split':'train2','dimension':'temporal_structure','alternatives':[asdict(r) for r in b.rows],'stat_association':association,'gdn_rows':rows}
                pack={**pack,'retrieval_hash':digest(pack)}
                ph=publish(directory/'retrieval'/f'{b.candidate_id}.json',pack)
            records.append({'candidate_id':b.candidate_id,'split':split,'structural_hash':sh,'pack_hash':ph,'global_seed_authority_hash':gh})
        del matrix,stat
    receipt=seal({'version':version,'schema':'xver_split_pure_evidence_freeze_v1','execution_hash':a['self_hash'],'candidate_hash':candidate['self_hash'],'N':len(pairs),'records':records,'structural_rows_per_pair':20,'global_rows_per_pair':5,'event_rows_exposed':0,'provider_calls':0,'credential_reads':0,'attack_accesses':0})
    publish(directory/'EVIDENCE_FROZEN.json',receipt);publish(PUB/f'HAI{version[:2]}_EVIDENCE_FREEZE_V1.json',receipt)
    print(json.dumps({'phase':'EVIDENCE_FROZEN','version':version,'N':len(pairs)}),flush=True)


def audit_fixed_portfolio(matrix,order,rules,file_id):
    """Observe already-frozen membership, never invoke guard/pruning again."""
    pos={s:i for i,s in enumerate(order)};events={};activity={}
    for i,r in enumerate(rules):
        v=dict(r.candidate_roles)
        events[i]=extract_candidate_specific_events_v1(matrix[:,pos[r.source]],threshold=v['source_step_threshold'],tolerance=v['source_stability_tolerance'])
        activity.setdefault(r.source,set()).update(e.event_index for e in events[i])
    records=[]
    for i,r in enumerate(rules):
        others=tuple(sorted({n for s,ns in activity.items() if s!=r.source for n in ns}))
        metric,seconds=census(source=matrix[:,pos[r.source]],target=matrix[:,pos[r.target]],semantic=r.semantic,roles=dict(r.candidate_roles),events=events[i],other_rows=others,alias=r.alias,slice_id='EV-POSTFREEZE-AUDIT')
        records.append((file_id,seconds,metric.passed,metric.failed,metric.abstained))
    return portfolio_census(tuple(records),{file_id:len(matrix)})


def execute_t0(version):
    a,context,candidate,roles,pairs=replay_authority(version);directory=run_directory(version)
    frozen=document(directory/'EVIDENCE_FROZEN.json');require(frozen['execution_hash']==a['self_hash'],'EVIDENCE_EXECUTION_BINDING')
    ids=tuple('EXP03B-CAND-'+digest({'source':s,'target':t})[:20] for s,t in pairs)
    outputs=[];admissions=[];admitted={}
    for cid in ids:
        x=hydrate(document(directory/'train1/structural'/f'{cid}.json'));y=hydrate(document(directory/'train2/structural'/f'{cid}.json'))
        for split in ('train1','train2'):
            expected=next(r for r in frozen['records'] if r['candidate_id']==cid and r['split']==split)
            require(sha256_file(directory/split/'structural'/f'{cid}.json')==expected['structural_hash'],'STRUCTURAL_BYTES')
        slot=directory/'t0_slots'/f'{cid}.json'
        if slot.exists():
            stored=document(slot)
            require(stored['execution_hash']==a['self_hash'] and stored['input_hash']==digest(asdict(x)), 'T0_REPLAY_IDENTITY')
            p=parse_proposal(stored['proposal'])
        else:
            p=t0(x)
            publish(slot,seal({'execution_hash':a['self_hash'],'input_hash':digest(asdict(x)),'candidate_id':cid,'proposal':proposal_document(p),'deterministic_scientific_executions':1}))
        outputs.append({'candidate_id':cid,'proposal':proposal_document(p),'proposal_hash':digest(proposal_document(p))})
        authority=Train2HiddenVerifierAuthorityV2(y,frozenset(r.evidence_slice_id for r in x.rows));v=verify(p,authority)
        ar=admit(p,authority,implementation_hash=digest(a['implementation_hashes']),config_hash=a['self_hash']) if v.status=='ACCEPTED' else None
        admitted[cid]=ar
        admissions.append({'candidate_id':cid,'status':v.status,'verifier':asdict(v),'admission_hash':ar.receipt['self_hash'] if ar else None,'admission_receipt':ar.receipt if ar else None})
    out=seal({'version':version,'provider_calls':0,'execution_hash':a['self_hash'],'records':outputs});publish(directory/'T0_OUTPUTS_FROZEN.json',out)
    adm=seal({'version':version,'provider_calls':0,'execution_hash':a['self_hash'],'outputs_hash':out['self_hash'],'records':admissions});publish(directory/'TRAIN2_ADMISSIONS_FROZEN.json',adm)
    print(json.dumps({'phase':'T0_ADMISSIONS_FROZEN','version':version,'N':len(ids),'admitted':sum(x is not None for x in admitted.values())}),flush=True)
    m1,order,r1=load_projection(version,'train1');m2,order2,r2=load_projection(version,'train2');m3,order3,r3=load_projection(version,'train3')
    require(order==order2==order3,'NORMAL_FEATURE_ORDER')
    confirm=m3 if version=='22.04' else m3[0:239370]
    h3=r3['projection_hash'] if version=='22.04' else digest({'projection':r3['projection_hash'],'rows':[0,239370]})
    ref_result=fit_and_confirm_mapped_union_v1(mapped_sources=tuple(roles['sources']),mapped_targets=tuple(roles['targets']),candidate_pairs=pairs,train1_matrix=m1,train2_matrix=m2,train3_matrix=confirm,feature_order=order,train1_read_receipt_hash=r1['projection_hash'],train2_read_receipt_hash=r2['projection_hash'],train3_read_receipt_hash=h3)
    publish(directory/'NORMAL_CONFIRMATION_PRIVATE.json',dict(ref_result.private_ledger))
    truth={cid:[] for cid in ids}
    for row in ref_result.private_ledger['directional_confirmation']:
        if row['confirmed']:
            cid='EXP03B-CAND-'+digest({'source':row['source'],'target':row['target']})[:20]
            truth[cid].append(SemanticTupleV1(row['source_direction'],row['target_direction'],row['horizon']))
    truth={cid:tuple(sorted(rows)) for cid,rows in truth.items()}
    ref=seal({'version':version,'provider_calls':0,'execution_hash':a['self_hash'],'normal_reference_kind':'FROZEN_NORMAL_CONFIRMED_RELATION_REFERENCE','input_hash':h3,'records':[{'candidate_id':cid,'relations':[asdict(s) for s in truth[cid]]} for cid in ids]});publish(directory/'NORMAL_REFERENCE_FROZEN.json',ref)
    ev=seal({'version':version,'provider_calls':0,'execution_hash':a['self_hash'],'outputs_hash':out['self_hash'],'admissions_hash':adm['self_hash'],'reference_hash':ref['self_hash'],'records':[{'candidate_id':cid,'admitted':admitted[cid] is not None,'semantic_exact':admitted[cid] is not None and admitted[cid].proposal.semantic_set()==truth[cid]} for cid in ids]});publish(directory/'SEMANTIC_EVALUATION_FROZEN.json',ev)
    cap=authorize_t0_binding(directory,version=version,candidate_ids=ids,execution_hash=a['self_hash'])
    sums=[{s:summarize_column(m[:,i]) for i,s in enumerate(order)} for m in (m1,m2)]
    bound=[];rejected=[];semantic_count=0
    for cid,pair in zip(ids,pairs):
        ar=admitted[cid]
        if ar is None:continue
        for index,r in enumerate(ar.proposal.rules):
            if r.semantic not in truth[cid]:continue
            semantic_count+=1
            try:
                bound.append(bind_t0_rule(cap,ar,index,pair=pair,train1_summary=(sums[0][pair[0]],sums[0][pair[1]]),train2_summary=(sums[1][pair[0]],sums[1][pair[1]])))
            except ValueError as error:
                require(str(error) in ('UNMATERIALIZABLE_NORMAL_OPTION','NONFINITE_NUMERIC_AUTHORITY','NUMERIC_SCALE_INVALID'),'UNEXPECTED_NUMERIC_FAILURE')
                rejected.append({'candidate_id':cid,'semantic':asdict(r.semantic),'status':str(error)})
    publish(directory/'NUMERIC_BOUND_PRIVATE.json',seal({'rules':[asdict(r) for r in bound],'rejections':rejected,'policy':POLICY,'evaluation_hash':ev['self_hash']}))
    descriptors=convert(private_root(),directory/'formal_v4',tuple(bound))
    if version=='22.04':guard_matrix,guard_order,gr=load_projection(version,'train4');guard_hash=gr['projection_hash'];file_id='HAI22_TRAIN4'
    else:guard_matrix=m3[239430:478801];guard_order=order;guard_hash=digest({'projection':r3['projection_hash'],'rows':[239430,478801]});file_id='HAI21_TRAIN3_BLOCK_B'
    require(guard_order==order,'GUARD_FEATURE_ORDER')
    states,burden=run_guard_portfolio(authority=Train4HiddenGuardAuthorityV1(guard_hash,file_id,len(guard_matrix)),matrix=guard_matrix,feature_order=order,rules=tuple(bound))
    retained=[r for r,s in zip(bound,states) if s[2]=='RETAINED'];retained_descriptors=[d for d,s in zip(descriptors,states) if s[2]=='RETAINED']
    guard_doc=seal({'version':version,'states':[{'candidate_id':cid,'semantic':asdict(s),'status':status} for cid,s,status in states],'retained_burden':safe(burden),'guard_projection_hash':guard_hash,'one_way':True});publish(directory/'GUARD_FROZEN.json',guard_doc)
    publish(directory/'PORTFOLIO_PRIVATE.json',seal({'version':version,'rules':[asdict(r) for r in retained],'descriptor_hashes':[d.descriptor_hash for d in retained_descriptors],'guard_hash':guard_doc['self_hash']}))
    metrics=strict_metrics(truth,{cid:ar.proposal.semantic_set() if ar else None for cid,ar in admitted.items()})
    public=seal({'schema':'xver_t0_heldout_candidate_v1','portfolio_id':f'HAI{version[:2]}_T0_DETERMINISTIC_HELDOUT_CANDIDATE_V1','version':version,'status':'HELDOUT_CANDIDATE_NOT_ATTACK_VALIDATED_NOT_PRODUCTION','candidate_hash':candidate['self_hash'],'candidate_N':len(ids),'evidence_hash':frozen['self_hash'],'T0_output_hash':out['self_hash'],'admissions_hash':adm['self_hash'],'reference_hash':ref['self_hash'],'evaluation_hash':ev['self_hash'],'guard_hash':guard_doc['self_hash'],'execution_hash':a['self_hash'],'T0_field_contract':'STRUCTURAL_ROWS_ONLY','raw_rule_sets':sum(bool(r['proposal']['rules']) for r in outputs),'train2_admitted_pairs':sum(ar is not None for ar in admitted.values()),'train2_admitted_rules':sum(len(ar.proposal.rules) for ar in admitted.values() if ar),'semantic_confirmed_rules':semantic_count,'numeric_bound_rules':len(bound),'numeric_rejection_counts':dict(Counter(r['status'] for r in rejected)),'Formal_V4_rules':len(descriptors),'guard_retained_rules':len(retained),'final_pair_count':len({(r.source,r.target) for r in retained}),'rules':[{'relation_id':d.relation_id,'source':r.source,'target':r.target,'semantic':asdict(r.semantic),'descriptor_hash':d.descriptor_hash} for r,d in zip(retained,retained_descriptors)],'strict_metrics':safe(metrics),'guard_state_counts':dict(Counter(s[2] for s in states)),'normal_burden':safe(burden),'provider_calls':0,'attack_accesses':0,'policy_searches':0,'source_commit':a['source_commit']})
    publish(PUB/f'HAI{version[:2]}_T0_PORTFOLIO_AUTHORITY_V1.json',public)
    if version=='22.04':
        for split in ('train5','train6'):
            matrix,fo,rr=load_projection(version,split);require(fo==order,'AUDIT_FEATURE_ORDER')
            result=audit_fixed_portfolio(matrix,fo,tuple(retained),'HAI22_'+split.upper())
            publish(PUB/f'HAI22_{split.upper()}_POSTFREEZE_AUDIT_V1.json',seal({'version':version,'split':split,'role':'POSTFREEZE_OBSERVATION_NO_SELECTION','portfolio_hash':public['self_hash'],'projection_hash':rr['projection_hash'],'burden':safe(result),'membership_changed':False,'numeric_changed':False,'provider_calls':0,'attack_accesses':0}))
    print(json.dumps({'phase':'T0_PORTFOLIO_FROZEN','version':version,'retained':len(retained),'hash':public['self_hash']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=('freeze','evidence','t0'));p.add_argument('--version',choices=('22.04','21.03'));args=p.parse_args()
    try:
        if args.phase=='freeze':freeze()
        elif args.phase=='evidence':evidence(args.version)
        else:execute_t0(args.version)
    except Exception as error:
        code=str(error) if type(error) is ValueError and str(error).replace('_','').isalnum() else 'REDACTED'
        print(json.dumps({'status':'BLOCKED_NORMAL_SEMANTIC_EXECUTION','error_type':type(error).__name__,'code':code}),flush=True);raise SystemExit(2)
