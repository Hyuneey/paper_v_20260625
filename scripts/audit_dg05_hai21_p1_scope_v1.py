"""Audit HAI21 against the historical exact-identity P1 scope without amendment."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def cb(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def d(v):return hashlib.sha256(cb(v)).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--scenario',type=Path,required=True);p.add_argument('--scope',type=Path,required=True);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args();s=json.loads(a.scenario.read_text());scope=json.loads(a.scope.read_text())
 if s.get('self_hash')!=d({k:v for k,v in s.items() if k!='self_hash'}):raise ValueError('SCENARIO_HASH')
 items=[x for x in scope['points'] if x.get('dataset_version')=='21.03']; exact={x['canonical_identity']:x['official_process'] for x in items}; decisions=[]
 for r in s['canonical_records']:
  memberships=[exact.get(x,'UNRESOLVED') for x in r['attacked_identities']]; status='P1_ELIGIBLE' if 'P1' in memberships else ('UNRESOLVED' if 'UNRESOLVED' in memberships else 'P1_NOT_ELIGIBLE'); decisions.append({'scenario_id':r['scenario_id'],'primary_status':status})
 counts={x:sum(d0['primary_status']==x for d0 in decisions) for x in ('P1_ELIGIBLE','P1_NOT_ELIGIBLE','UNRESOLVED')}; out={'schema':'hai21_p1_existing_semantic_audit_v1','status':'PENDING_USER_DECISION' if counts['UNRESOLVED'] else 'PASS','verdict':'HAI21_P1_SCOPE_REQUIRES_VERSION_SPECIFIC_PROSPECTIVE_AMENDMENT' if counts['UNRESOLVED'] else 'HAI21_EXISTING_EXACT_SCOPE_SUFFICIENT','scenario_authority_sha256':s['self_hash'],'historical_scope_sha256':'0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619','classification_counts':counts,'normative_semantic':'HISTORICAL_EXACT_CANONICAL_FEATURE_IDENTITY_ONLY','new_amendment_automatically_created':False,'heldout_predictions_observed':0,'heldout_metrics_observed':0};out['self_hash']=d(out);a.public_output.write_bytes(cb(out)+b'\n');print(json.dumps({'status':out['status'],'counts':counts,'hash':out['self_hash']},sort_keys=True))
if __name__=='__main__':main()
