"""Post-freeze adapter for the frozen, triangulated HAI scenario authority.

The adapter is intentionally scenario-only: it accepts no method, prediction,
or detector input.  It is a prospective V11 component and does not alter the
historical V2 custodian implementation bound by V10.
"""
from __future__ import annotations
import hashlib, json
from typing import Any, Mapping

REQUIRED_STATE = "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED"
EXPECTED_COUNTS = {"HAI23_TEST2_PRIMARY_HELDOUT_V1":38,"HAI22_EXTERNAL_REPLICATION_V1":58,"HAI21_EXTERNAL_REPLICATION_V1":50}

class OfficialHAIScenarioAdapterError(ValueError): pass
def canonical_bytes(value: Any)->bytes:return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')
def digest(value: Any)->str:return hashlib.sha256(canonical_bytes(value)).hexdigest()
def validate_unified_authority(value:Mapping[str,Any])->None:
 if value.get('self_hash')!=digest({k:v for k,v in value.items() if k!='self_hash'}):raise OfficialHAIScenarioAdapterError('UNIFIED_SCENARIO_AUTHORITY_SELF_HASH_MISMATCH')
 if value.get('schema')!='hai_official_source_triangulated_scenario_authority_private_v1':raise OfficialHAIScenarioAdapterError('UNIFIED_SCENARIO_AUTHORITY_SCHEMA_REQUIRED')
 records=value.get('canonical_records');
 if not isinstance(records,list) or len(records)!=146:raise OfficialHAIScenarioAdapterError('UNIFIED_146_CENSUS_REQUIRED')
 if len({item.get('scenario_id') for item in records})!=146 or any(not item.get('closed_intervals') for item in records):raise OfficialHAIScenarioAdapterError('UNIFIED_SCENARIO_BINDING_REQUIRED')
def adapt_frozen_hai_authority(*, unified_authority:Mapping[str,Any], predecessor_state:Mapping[str,Any])->dict[str,Any]:
 """Expose only the custodian's canonical input shape after the freeze gate."""
 if predecessor_state.get('state')!=REQUIRED_STATE:raise OfficialHAIScenarioAdapterError('SCENARIO_SOURCE_ACCESS_BEFORE_GLOBAL_FREEZE')
 validate_unified_authority(unified_authority)
 output=[]
 for row in unified_authority['canonical_records']:
  output.append({'panel_id':row['panel_id'],'dataset_version':row['dataset_version'],'file_id':row['physical_file_id'],'scenario_id':row['scenario_id'],'closed_intervals':[[x['start'],x['end']] for x in row['closed_intervals']],'attacked_identities':list(row['attacked_identities']),'explicit_affected_processes':list(row['explicit_affected_processes'])})
 counts={p:sum(row['panel_id']==p for row in output) for p in EXPECTED_COUNTS}
 if counts!=EXPECTED_COUNTS:raise OfficialHAIScenarioAdapterError('FROZEN_PANEL_CENSUS_REQUIRED')
 return {'schema':'hai_official_scenario_metadata_raw_v3','adapter_id':'HAI_OFFICIAL_TRIANGULATED_SCENARIO_AUTHORITY_V1','authority_hash':unified_authority['self_hash'],'records':sorted(output,key=lambda x:(x['panel_id'],x['file_id'],x['scenario_id'])),'prediction_capability':False}
