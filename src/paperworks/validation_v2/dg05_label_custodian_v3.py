"""V11 scenario-authority custodian preflight.

This version deliberately leaves V2 historical bytes untouched.  It provides
the authority gate that the eventual fresh-process launcher must invoke before
passing canonical scenario records to the existing isolated output writer.
"""
from __future__ import annotations
import hashlib,json
from typing import Any,Mapping
from .dg05_hai_scenario_adapter_v1 import adapt_frozen_hai_authority,validate_unified_authority
class CustodianV3Error(ValueError):pass
def cb(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def d(v:Any)->str:return hashlib.sha256(cb(v)).hexdigest()
def _valid(v:Mapping[str,Any],schema:str)->None:
 if v.get('self_hash')!=d({k:x for k,x in v.items() if k!='self_hash'}) or v.get('schema')!=schema:raise CustodianV3Error('P1_AUTHORITY_REPLAY_FAILED')
def prepare_custodian_input_v3(*,unified_scenario:Mapping[str,Any],unified_p1:Mapping[str,Any],predecessor_state:Mapping[str,Any])->dict[str,Any]:
 validate_unified_authority(unified_scenario);_valid(unified_p1,'hai_p1_direct_target_denominator_authority_v2')
 decisions=unified_p1.get('decisions',[])
 if len(decisions)!=146 or any(x.get('eligibility_status')=='UNRESOLVED' for x in decisions):raise CustodianV3Error('P1_DENOMINATOR_INCOMPLETE_FAIL_CLOSED')
 raw=adapt_frozen_hai_authority(unified_authority=unified_scenario,predecessor_state=predecessor_state)
 return {'schema':'dg05_v11_custodian_scenario_input_v1','scenario_adapter_id':raw['adapter_id'],'scenario_authority_hash':unified_scenario['self_hash'],'p1_authority_hash':unified_p1['self_hash'],'records':raw['records'],'prediction_capability':False,'dec031_preserved':True}
