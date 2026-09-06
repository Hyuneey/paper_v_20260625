"""DEC-037 HAI21-only source-rooted direct-target P1 authority."""
from __future__ import annotations
import hashlib,json,re
from typing import Any,Mapping
DECISION_ID='DEC-037';SCENARIO_HASH='27ba9f39571bb55954388ccb3616837c6d29e34ac42aa96b4164a9605f2a90a3';MANUAL_HASH='0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556';_P=re.compile(r'^(P[1-4])-')
def cb(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(v:Any)->str:return hashlib.sha256(cb(v)).hexdigest()
def selfh(v:dict[str,Any])->dict[str,Any]:
 b=dict(v);b.pop('self_hash',None);return {**b,'self_hash':digest(b)}
def tok(v:str)->str:return hashlib.sha256(v.encode()).hexdigest()
def build_target_process_authority(*,scenario_authority:Mapping[str,Any],decision_hash:str)->dict[str,Any]:
 if scenario_authority.get('self_hash')!=SCENARIO_HASH:raise ValueError('HAI21_SCENARIO_AUTHORITY_BINDING_REQUIRED')
 if len(decision_hash)!=64:raise ValueError('DEC037_HASH_REQUIRED')
 source={}
 for row in scenario_authority['canonical_records']:
  ts,cs=row['attacked_identities'],row['target_controller_components']
  if len(ts)!=len(cs):raise ValueError('HAI21_TARGET_CONTROLLER_ROW_BINDING_INCOMPLETE')
  for t,c in zip(ts,cs):source.setdefault(t,set()).add(c)
 rec=[]
 for raw in sorted(source):
  controllers=sorted(source[raw]);processes={m.group(1) for c in controllers if (m:=_P.match(c))}; membership=next(iter(processes)) if len(processes)==1 else 'UNRESOLVED';r={'raw_official_target_identity_hash':tok(raw),'target_namespace':'OTHER_OFFICIAL_HAI21_TARGET_IDENTITY','canonical_hai_feature_identity':None,'official_controller_identity_hashes':[tok(x) for x in controllers],'official_process_membership':membership,'source_artifact':'hai_dataset_technical_details.pdf','source_sha256':MANUAL_HASH,'evidence_type':'OFFICIAL_HAI21_MANUAL_TARGET_CONTROLLER_COLUMN_ROW_BINDING' if membership!='UNRESOLVED' else 'OFFICIAL_HAI21_CONTROLLER_MEMBERSHIP_CONFLICT_OR_ABSENCE','mapping_rule':'HAI21_MANUAL_ROW_BOUND_TARGET_CONTROLLER_PROCESS_MEMBERSHIP_NO_TARGET_ALIAS','heuristic_alias':False};r['record_hash']=digest(r);rec.append(r)
 return selfh({'schema':'hai21_official_direct_target_process_authority_v1','decision_id':DECISION_ID,'decision_hash':decision_hash,'scenario_authority_sha256':SCENARIO_HASH,'historical_predecessor':{'authority_id':'FULL_PROCESS_SCOPE_AUTHORITY_V1','authority_sha256':'0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619'},'official_source_roots':{'technical_manual_sha256':MANUAL_HASH},'records':rec,'forbidden':['CROSS_VERSION_MAPPING_REUSE','TARGET_PREFIX_INFERENCE','SUBSTRING_INFERENCE','CASE_OR_DELIMITER_ALIAS','EDIT_DISTANCE','CANONICAL_FEATURE_FABRICATION']})
def classify(*,scenario_authority:Mapping[str,Any],target_authority:Mapping[str,Any],decision_hash:str)->dict[str,Any]:
 if target_authority.get('decision_hash')!=decision_hash:raise ValueError('DEC037_BINDING_REQUIRED')
 mapping={r['raw_official_target_identity_hash']:r['official_process_membership'] for r in target_authority['records']}; ds=[]
 for s in scenario_authority['canonical_records']:
  ms=[mapping.get(tok(x),'UNRESOLVED') for x in s['attacked_identities']];status='P1_ELIGIBLE' if 'P1' in ms else ('UNRESOLVED' if 'UNRESOLVED' in ms else 'P1_NOT_ELIGIBLE');ds.append({'scenario_id':s['scenario_id'],'primary_status':status,'direct_target_set_hash':digest(sorted(tok(x) for x in s['attacked_identities']))})
 return selfh({'schema':'hai21_p1_direct_target_eligibility_authority_v2','decision_id':DECISION_ID,'decision_hash':decision_hash,'scenario_authority_sha256':scenario_authority['self_hash'],'target_process_authority_sha256':target_authority['self_hash'],'multi_target_aggregation':'ANY_VERIFIED_P1_DIRECT_TARGET','unknown_handling':'UNRESOLVED_UNLESS_ANY_VERIFIED_P1_DIRECT_TARGET','decisions':ds})
