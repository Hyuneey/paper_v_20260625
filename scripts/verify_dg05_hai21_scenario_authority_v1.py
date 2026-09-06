"""Independent DEC-035 HAI21 reconstruction; no builder imports."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, re
from datetime import datetime
from pathlib import Path
import pdfplumber

H='0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556'; E={1:5,2:20,3:8,4:5,5:12}
def cb(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def d(v): return hashlib.sha256(cb(v)).hexdigest()
def sh(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manual(p):
    if sh(p)!=H: raise ValueError('OFFICIAL_MANUAL_HASH_MISMATCH')
    out=[]; current=None
    with pdfplumber.open(p) as pdf:
      for page in range(36,39):
       for table in pdf.pages[page].extract_tables():
        for raw in table:
          cells=[x.strip() if x else '' for x in raw]; ids=[x for x in cells if re.fullmatch(r'A[1-5][0-9]{2}',x)]; aps=[x for x in cells if re.fullmatch(r'AP[0-9]+',x)]; cs=[x for x in cells if re.fullmatch(r'P[1-4]-.*',x)]; ts=[x for x in cells if re.fullmatch(r'(?:P[1-4]_[A-Za-z0-9]|[0-9]{4}-).*',x)]
          if ids:
            times=[x for x in cells if re.fullmatch(r'[0-9]{1,2}:[0-9]{2}',x)]; pos=cells.index(times[0]); dur=[int(x) for x in cells[pos+1:] if x.isdecimal()]
            if len(ids)!=1 or len(times)!=1 or len(dur)!=1: raise ValueError('HAI21_INDEPENDENT_MANUAL_PARSE_FAILURE')
            current={'official_occurrence_id':ids[0],'manual_start_minute':times[0],'manual_duration_seconds':dur[0],'scenario_components':aps,'target_controller_components':cs,'attacked_identities':ts}; out.append(current)
          elif current is not None and (aps or cs or ts): current['scenario_components']+=aps; current['target_controller_components']+=cs; current['attacked_identities']+=ts
    if len(out)!=50: raise ValueError('HAI21_INDEPENDENT_MANUAL_CENSUS')
    return out
def ranges(p):
    out=[]
    with gzip.open(p,'rt',encoding='utf-8',newline='') as f:
      r=csv.reader(f); h=next(r); ti,ai=h.index('time'),h.index('attack'); start=end=None
      for row in r:
       if row[ai]=='1' and start is None: start=row[ti]
       if row[ai]=='1': end=row[ti]
       elif start is not None: out.append({'start':start,'end':end,'duration_seconds':int((datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds())}); start=end=None
      if start is not None: out.append({'start':start,'end':end,'duration_seconds':int((datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds())})
    return out
def minute(v): q=datetime.fromisoformat(v); return f'{q.hour}:{q.minute:02d}'
def main():
 p=argparse.ArgumentParser();p.add_argument('--official-root',type=Path,required=True);p.add_argument('--private-authority',type=Path,required=True);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args(); auth=json.loads(a.private_authority.read_text())
 if auth.get('self_hash')!=d({k:v for k,v in auth.items() if k!='self_hash'}): raise ValueError('SELF_HASH')
 rows=manual(a.official_root/'hai_dataset_technical_details.pdf'); records=[]; residual=[]
 for n,c in E.items():
  ms=[x for x in rows if x['official_occurrence_id'][1]==str(n)]; ls=ranges(a.official_root/'hai-21.03'/f'test{n}.csv.gz'); used=set(); match={}
  for mi,m in enumerate(ms):
   cand=[i for i,x in enumerate(ls) if i not in used and minute(x['start'])==m['manual_start_minute'].lstrip('0') and x['duration_seconds']==m['manual_duration_seconds']-1]
   if len(cand)==1: used.add(cand[0]);match[mi]=(cand[0],{'join_kind':'UNIQUE_COMPATIBLE_MANUAL_LABEL_CORROBORATION'})
   elif len(cand)>1: raise ValueError('HAI21_INDEPENDENT_AMBIGUOUS')
  remain_m=[i for i in range(c) if i not in match];remain_l=[i for i in range(c) if i not in used]
  if remain_m:
   expected={2:'A209',5:'A512'}.get(n)
   if len(remain_m)!=1 or len(remain_l)!=1 or ms[remain_m[0]]['official_occurrence_id']!=expected: raise ValueError('HAI21_RESIDUAL_OCCURRENCE_MAPPING_AMBIGUOUS')
   mi,li=remain_m[0],remain_l[0]
   if any((mii<mi)!=(datetime.fromisoformat(ls[lii]['start'])<datetime.fromisoformat(ls[li]['start'])) for mii,(lii,_) in match.items()): raise ValueError('HAI21_RESIDUAL_OCCURRENCE_MAPPING_AMBIGUOUS')
   proof={'join_kind':'UNIQUE_RESIDUAL_OFFICIAL_SOURCE_BIJECTION','same_physical_file':True,'manual_file_census':c,'label_range_census':c,'compatible_pairs_preassigned':len(match),'unmatched_manual_count':1,'unmatched_label_range_count':1,'chronological_neighborhood_noncontradictory':True,'alternative_complete_bijections':0};match[mi]=(li,proof);residual.append(ms[mi]['official_occurrence_id'])
  for mi,m in enumerate(ms):
   li,proof=match[mi];x=ls[li];records.append({'dataset_version':'21.03','panel_id':'HAI21_EXTERNAL_REPLICATION_V1','physical_file_id':f'HAI21_TEST{n}','scenario_id':f"HAI21_03:{m['official_occurrence_id']}",'official_occurrence_id':m['official_occurrence_id'],'closed_intervals':[{'start':x['start'],'end':x['end']}],'attacked_identities':m['attacked_identities'],'explicit_affected_processes':[],'manual_start_minute':m['manual_start_minute'],'manual_duration_seconds':m['manual_duration_seconds'],'label_duration_seconds':x['duration_seconds'],'scenario_components':m['scenario_components'],'target_controller_components':m['target_controller_components'],'join_proof':proof})
 if records!=auth['canonical_records'] or sorted(residual)!=['A209','A512']: raise ValueError('HAI21_INDEPENDENT_CANONICAL_REPLAY_MISMATCH')
 out={'schema':'hai21_official_scenario_independent_replay_receipt_v1','status':'PASS','private_authority_sha256':auth['self_hash'],'canonical_records':50,'residual_occurrences':residual,'independent_parser':'SEPARATE_IMPLEMENTATION_NO_BUILDER_IMPORT','heldout_predictions_observed':0,'heldout_metrics_observed':0};out['self_hash']=d(out);a.public_output.write_bytes(cb(out)+b'\n');print(json.dumps({'status':'PASS','receipt_hash':out['self_hash']},sort_keys=True))
if __name__=='__main__':main()
