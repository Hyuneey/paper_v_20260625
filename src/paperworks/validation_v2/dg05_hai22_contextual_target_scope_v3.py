"""Context-preserving DEC-036 HAI22 target-instance authority.

The predecessor keyed evidence solely by raw target text.  V3 preserves the
official occurrence and row-bound controller context, so text reused by
distinct official attack rows is never conflated into a global ownership claim.
"""
from __future__ import annotations
import hashlib,json,re
from typing import Any,Mapping
SCENARIO='34c53aef62a248a4d384083f187e47a4854df045d762533a4b8939fe54c707fb';DEC='DEC-036';MANUAL='0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556';P=re.compile(r'^(P[1-4])-')
def cb(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def d(v:Any)->str:return hashlib.sha256(cb(v)).hexdigest()
def selfh(v:dict[str,Any])->dict[str,Any]:b=dict(v);b.pop('self_hash',None);return {**b,'self_hash':d(b)}
def h(v:str)->str:return hashlib.sha256(v.encode()).hexdigest()
def build(*,scenario:Mapping[str,Any],decision_hash:str,predecessor_hash:str)->dict[str,Any]:
 if scenario.get('self_hash')!=SCENARIO:raise ValueError('HAI22_SCENARIO_ROOT_REQUIRED')
 records=[]
 for row in scenario['canonical_records']:
  targets,controllers=row['attacked_identities'],row['target_controller_components']
  if len(targets)!=len(controllers):raise ValueError('HAI22_TARGET_CONTROLLER_PAIRING_GRAMMAR_AMBIGUOUS')
  for index,(target,controller) in enumerate(zip(targets,controllers)):
   m=P.match(controller)
   if m is None:raise ValueError('HAI22_CONTROLLER_PROCESS_AUTHORITY_INCOMPLETE')
   record={'dataset_version':'22.04','official_occurrence_id':row['official_occurrence_id'],'raw_official_target_identity_hash':h(target),'raw_target_position':index,'official_controller_identity_hash':h(controller),'source_row_hash':d({'id':row['official_occurrence_id'],'target':target,'controller':controller,'position':index}),'official_process_memberships':[m.group(1)],'source_artifact':'hai_dataset_technical_details.pdf','source_sha256':MANUAL,'evidence_type':'OFFICIAL_HAI22_OCCURRENCE_LOCAL_TARGET_CONTROLLER_ROW_BINDING','heuristic_alias':False};record['record_hash']=d(record);records.append(record)
 if len({(r['official_occurrence_id'],r['raw_target_position']) for r in records})!=len(records):raise ValueError('DUPLICATE_CONTEXTUAL_TARGET_INSTANCE')
 return selfh({'schema':'hai22_official_direct_target_process_authority_v3','decision_id':DEC,'decision_hash':decision_hash,'scenario_authority_sha256':scenario['self_hash'],'predecessors':{'target_process_authority_v1':'25a358642ac6e3eac5a372b0ec8e3b568d82f379c4ec766c7cba27d30a8cad20','eligibility_authority_v2':'b6d9450dd600ceb95e40a26e1ad62e3f26c3b47fa39c33773766c5ff78e7b3f5','private_bundle':'4671578fbecad6f2cc1d951ecde01eba502620af2ce202ac9fe2bcb14026a4ee','predecessor_superseded_reason':'CONTEXT_PRESERVING_OFFICIAL_SOURCE_REPRESENTATION'},'records':records,'lossy_target_authority_key_confirmed':True,'forbidden':['RAW_TARGET_ONLY_GLOBAL_OWNERSHIP','CROSS_PRODUCT_TARGET_CONTROLLER_PAIRING','CROSS_VERSION_MAPPING_REUSE','HEURISTIC_ALIAS']})
def classify(*,scenario:Mapping[str,Any],authority:Mapping[str,Any])->dict[str,Any]:
 index={(r['official_occurrence_id'],r['raw_target_position']):r for r in authority['records']};out=[]
 for row in scenario['canonical_records']:
  memberships=[]
  for pos,_ in enumerate(row['attacked_identities']):
   r=index.get((row['official_occurrence_id'],pos));memberships+=r['official_process_memberships'] if r else ['UNRESOLVED']
  status='P1_ELIGIBLE' if 'P1' in memberships else ('UNRESOLVED' if 'UNRESOLVED' in memberships else 'P1_NOT_ELIGIBLE');out.append({'scenario_id':row['scenario_id'],'primary_status':status,'contextual_target_set_hash':d(sorted((r['source_row_hash'] for r in authority['records'] if r['official_occurrence_id']==row['official_occurrence_id'])) )})
 return selfh({'schema':'hai22_p1_direct_target_eligibility_authority_v3','decision_id':DEC,'decision_hash':authority['decision_hash'],'scenario_authority_sha256':scenario['self_hash'],'target_process_authority_sha256':authority['self_hash'],'multi_target_aggregation':'ANY_VERIFIED_P1_DIRECT_TARGET','unknown_handling':'UNRESOLVED_UNLESS_ANY_VERIFIED_P1_DIRECT_TARGET','decisions':out})
