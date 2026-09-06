"""Independent HAI21 DEC-037 replay without importing the primary mapper."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def cb(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def d(v):return hashlib.sha256(cb(v)).hexdigest()
def token(v):return hashlib.sha256(v.encode()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--scenario',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--decision',type=Path,required=True);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args();s=json.loads(a.scenario.read_text());b=json.loads(a.bundle.read_text());de=json.loads(a.decision.read_text())
 if s['self_hash']!='27ba9f39571bb55954388ccb3616837c6d29e34ac42aa96b4164a9605f2a90a3' or b.get('self_hash')!=d({k:v for k,v in b.items() if k!='self_hash'}):raise ValueError('UPSTREAM_AUTHORITY_REPLAY_FAILURE')
 t,e=b['target_process_authority'],b['eligibility_authority']
 if t['decision_hash']!=de['self_hash'] or e['decision_hash']!=de['self_hash']:raise ValueError('DEC037_REPLAY_FAILURE')
 m={r['raw_official_target_identity_hash']:r['official_process_membership'] for r in t['records']};re=[]
 for row in s['canonical_records']:
  xs=[m.get(token(x),'UNRESOLVED') for x in row['attacked_identities']];status='P1_ELIGIBLE' if 'P1' in xs else ('UNRESOLVED' if 'UNRESOLVED' in xs else 'P1_NOT_ELIGIBLE');re.append({'scenario_id':row['scenario_id'],'primary_status':status,'direct_target_set_hash':d(sorted(token(x) for x in row['attacked_identities']))})
 if re!=e['decisions']:raise ValueError('HAI21_INDEPENDENT_P1_REPLAY_MISMATCH')
 counts={x:sum(r['primary_status']==x for r in re) for x in ('P1_ELIGIBLE','P1_NOT_ELIGIBLE','UNRESOLVED')};out={'schema':'hai21_p1_dec037_independent_replay_receipt_v1','status':'PASS','decision_hash':de['self_hash'],'scenario_authority_sha256':s['self_hash'],'target_process_authority_sha256':t['self_hash'],'eligibility_authority_sha256':e['self_hash'],'classification_counts':counts,'independent_mapper':'LOCAL_HASH_MAP_NO_PRIMARY_MAPPER_IMPORT','heldout_predictions_observed':0,'heldout_metrics_observed':0};out['self_hash']=d(out);a.public_output.write_bytes(cb(out)+b'\n');print(json.dumps({'hash':out['self_hash'],'counts':counts},sort_keys=True))
if __name__=='__main__':main()
