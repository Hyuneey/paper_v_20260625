"""Combine independently frozen version scenario roots without reparsing them."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def cb(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def d(v): return hashlib.sha256(cb(v)).hexdigest()
def selfh(v): return {**v,'self_hash':d(v)}
def load(p):
 v=json.loads(p.read_text());
 if v.get('self_hash')!=d({k:x for k,x in v.items() if k!='self_hash'}): raise ValueError('UPSTREAM_SCENARIO_SELF_HASH_MISMATCH')
 return v
def main():
 p=argparse.ArgumentParser();p.add_argument('--hai23',type=Path,required=True);p.add_argument('--hai22',type=Path,required=True);p.add_argument('--hai21',type=Path,required=True);p.add_argument('--private-output',type=Path,required=True);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args(); roots={'23.05':load(a.hai23),'22.04':load(a.hai22),'21.03':load(a.hai21)}; expected={'23.05':38,'22.04':58,'21.03':50}; records=[]
 for v,root in roots.items():
  if len(root['canonical_records'])!=expected[v]:raise ValueError('VERSION_CENSUS_MISMATCH')
  records+=root['canonical_records']
 if len(records)!=146 or len({x['scenario_id'] for x in records})!=146: raise ValueError('UNIFIED_SCENARIO_ID_COLLISION')
 if any(not x['closed_intervals'] for x in records):raise ValueError('UNBOUND_INTERVAL')
 authority=selfh({'schema':'hai_official_source_triangulated_scenario_authority_private_v1','status':'PRIVATE_CANONICAL_AUTHORITY','version_roots':{v:x['self_hash'] for v,x in roots.items()},'version_counts':expected,'canonical_records':records,'p1_status':'SEPARATE_EXTENSION_LAYER'})
 a.private_output.parent.mkdir(parents=True,exist_ok=True);a.private_output.write_bytes(cb(authority)+b'\n'); receipt=selfh({'schema':'hai_official_source_triangulated_scenario_authority_public_receipt_v1','status':'PASS','private_authority_sha256':authority['self_hash'],'version_roots':authority['version_roots'],'version_counts':expected,'total':146,'duplicate_ids':0,'unbound_intervals':0,'ambiguous_joins':0,'heldout_predictions_observed':0,'heldout_metrics_observed':0});a.public_output.write_bytes(cb(receipt)+b'\n');print(json.dumps({'private':authority['self_hash'],'public':receipt['self_hash'],'total':146},sort_keys=True))
if __name__=='__main__':main()
