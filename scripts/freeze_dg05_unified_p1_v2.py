"""Join frozen version-specific P1 decisions; no target mapper is shared."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def cb(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def d(v):return hashlib.sha256(cb(v)).hexdigest()
def selfh(v):return {**v,'self_hash':d(v)}
def load(p):
 v=json.loads(p.read_text());
 if v.get('self_hash')!=d({k:x for k,x in v.items() if k!='self_hash'}):raise ValueError('UPSTREAM_SELF_HASH_MISMATCH')
 return v
def main():
 p=argparse.ArgumentParser();p.add_argument('--hai23',type=Path,required=True);p.add_argument('--hai22',type=Path,required=True);p.add_argument('--hai21',type=Path,required=True);p.add_argument('--private-output',type=Path,required=True);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args();x23,x22,x21=load(a.hai23),load(a.hai22),load(a.hai21); groups=[('23.05',x23['records'],x23['self_hash'],'eligibility'),('22.04',x22['eligibility_authority']['decisions'],x22['eligibility_authority']['self_hash'],'primary_status'),('21.03',x21['eligibility_authority']['decisions'],x21['eligibility_authority']['self_hash'],'primary_status')];rows=[]; roots={}
 for version,records,root,status_key in groups:
  roots[version]=root
  for r in records:
   target_hash=r.get('direct_target_set_hash',r.get('contextual_target_set_hash'))
   if target_hash is None:raise ValueError('VERSION_TARGET_SET_HASH_REQUIRED')
   rows.append({'scenario_id':r['scenario_id'],'dataset_version':version,'eligibility_status':r[status_key],'direct_target_set_hash':target_hash,'version_decision_authority_sha256':root})
 if len(rows)!=146 or len({r['scenario_id'] for r in rows})!=146 or any(r['eligibility_status']=='UNRESOLVED' for r in rows):raise ValueError('UNIFIED_P1_DETERMINISTIC_CENSUS_REQUIRED')
 out=selfh({'schema':'hai_p1_direct_target_denominator_authority_v2','status':'PASS','version_decision_roots':roots,'aggregation':'VERSION_SPECIFIC_ANY_VERIFIED_P1_DIRECT_TARGET','decisions':sorted(rows,key=lambda r:r['scenario_id'])});a.private_output.parent.mkdir(parents=True,exist_ok=True);a.private_output.write_bytes(cb(out)+b'\n');counts={s:sum(r['eligibility_status']==s for r in rows) for s in ('P1_ELIGIBLE','P1_NOT_ELIGIBLE','UNRESOLVED')};receipt=selfh({'schema':'hai_p1_direct_target_denominator_public_receipt_v2','status':'PASS','private_authority_sha256':out['self_hash'],'version_decision_roots':roots,'total':146,'classification_counts':counts,'heldout_predictions_observed':0,'heldout_metrics_observed':0});a.public_output.write_bytes(cb(receipt)+b'\n');print(json.dumps({'authority':out['self_hash'],'receipt':receipt['self_hash'],'counts':counts},sort_keys=True))
if __name__=='__main__':main()
