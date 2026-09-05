"""Method-blind P1 scenario eligibility classifier, frozen before DG-05."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

STATUSES=frozenset({'P1_ELIGIBLE','CROSS_PROCESS_P1_RELEVANT','OUT_OF_SCOPE','UNRESOLVED'})
FORBIDDEN=frozenset({'prediction','alarm','hit','miss','rule','score','detector','metric','signal_response'})


@dataclass(frozen=True)
class OfficialScenarioMetadataV1:
    dataset_version:str
    file_id:str
    scenario_id:str
    attacked_identities:tuple[str,...]
    explicit_affected_processes:tuple[str,...]=()


def classify_p1_scenario_v1(scenario:OfficialScenarioMetadataV1, mapping:Mapping[str,str], *, mapping_authority_hash: str)->dict[str,object]:
    """Classify solely from official identities and a frozen mapping.

    Mapping values are P1, OUT_OF_SCOPE, or UNRESOLVED.  Exact and verified
    aliases must already have been resolved when that authority is frozen.
    """
    if type(scenario) is not OfficialScenarioMetadataV1 or not scenario.dataset_version or not scenario.file_id or not scenario.scenario_id or not scenario.attacked_identities:
        raise ValueError('OFFICIAL_SCENARIO_AUTHORITY_REQUIRED')
    if len(mapping_authority_hash) != 64 or any(ch not in '0123456789abcdef' for ch in mapping_authority_hash):
        raise ValueError('FROZEN_MAPPING_AUTHORITY_REQUIRED')
    if any(not isinstance(x,str) or not x for x in (*scenario.attacked_identities,*scenario.explicit_affected_processes)):
        raise ValueError('INVALID_OFFICIAL_IDENTITY')
    identities=tuple(sorted(set(scenario.attacked_identities)))
    observed=[]
    for identity in identities:
        status=mapping.get(identity,'UNRESOLVED')
        if status not in ('P1','OUT_OF_SCOPE','UNRESOLVED'):raise ValueError('INVALID_FROZEN_MAPPING')
        observed.append(status)
    if 'P1' in observed:status='P1_ELIGIBLE'
    elif 'UNRESOLVED' in observed:status='UNRESOLVED'
    elif 'P1' in scenario.explicit_affected_processes:status='CROSS_PROCESS_P1_RELEVANT'
    else:status='OUT_OF_SCOPE'
    return {'dataset_version':scenario.dataset_version,'file_id':scenario.file_id,'scenario_id':scenario.scenario_id,
            'status':status,'attacked_identity_count':len(identities),'mapping_authority_hash':mapping_authority_hash}


def assert_method_blind_payload_v1(payload:Mapping[str,object])->None:
    lowered={str(key).lower() for key in payload}
    if any(any(token in key for token in FORBIDDEN) for key in lowered):raise ValueError('METHOD_OUTCOME_TAINT')


def _canonical(value:Mapping[str,Any])->bytes:
    return json.dumps(dict(value),sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def _hash(value:Mapping[str,Any])->str:return sha256(_canonical(value)).hexdigest()
def _sha(value:str,field:str)->None:
    if type(value) is not str or len(value)!=64 or any(ch not in '0123456789abcdef' for ch in value):raise ValueError(f'{field} must be sha256')
def _gitsha(value:str,field:str)->None:
    if type(value) is not str or len(value)!=40 or any(ch not in '0123456789abcdef' for ch in value):raise ValueError(f'{field} must be full git sha')
def _identity(value:str,field:str)->None:
    if type(value) is not str or not value:raise ValueError(f'invalid {field}')


MAPPING_STATES=frozenset({'EXACT_MATCH','VERIFIED_ALIAS','ABSENT','UNIT_MISMATCH','ROLE_MISMATCH','SEMANTIC_MISMATCH','DATATYPE_MISMATCH','SAMPLE_RATE_MISMATCH','UNRESOLVED'})
MAPPING_SCOPES=frozenset({'P1','OUT_OF_SCOPE','UNRESOLVED'})


@dataclass(frozen=True,order=True)
class P1MappingEntryV2:
    official_identity:str
    scope:str
    mapping_state:str
    provenance_hash:str
    def validate(self)->None:
        _identity(self.official_identity,'official_identity')
        if self.scope not in MAPPING_SCOPES or self.mapping_state not in MAPPING_STATES:raise ValueError('invalid frozen mapping entry')
        if self.scope=='P1' and self.mapping_state not in ('EXACT_MATCH','VERIFIED_ALIAS'):raise ValueError('P1 requires exact or verified mapping')
        _sha(self.provenance_hash,'provenance_hash')
    def document(self)->dict[str,str]:return dict(self.__dict__)


@dataclass(frozen=True)
class FrozenP1MappingAuthorityV2:
    dataset_version:str
    entries:tuple[P1MappingEntryV2,...]
    official_mapping_source_hash:str
    source_commit:str
    def body(self)->dict[str,Any]:
        return {'schema':'frozen_p1_mapping_authority_v2','dataset_version':self.dataset_version,
                'entries':[item.document() for item in self.entries],
                'official_mapping_source_hash':self.official_mapping_source_hash,'source_commit':self.source_commit}
    def document(self)->dict[str,Any]:
        body=self.body();return {**body,'self_hash':_hash(body)}
    def validate(self)->None:
        _identity(self.dataset_version,'dataset_version');_sha(self.official_mapping_source_hash,'official_mapping_source_hash');_gitsha(self.source_commit,'source_commit')
        if not self.entries or tuple(sorted(self.entries))!=self.entries or len({item.official_identity for item in self.entries})!=len(self.entries):raise ValueError('canonical unique mapping entries required')
        for item in self.entries:item.validate()
    def lookup(self,identity:str)->P1MappingEntryV2|None:
        self.validate()
        return next((item for item in self.entries if item.official_identity==identity),None)


@dataclass(frozen=True)
class OfficialScenarioMetadataV2:
    dataset_version:str
    file_id:str
    scenario_id:str
    attacked_identities:tuple[str,...]
    explicit_affected_processes:tuple[str,...]
    official_source_hash:str
    scenario_authority_hash:str
    def validate(self)->None:
        for value,name in ((self.dataset_version,'dataset_version'),(self.file_id,'file_id'),(self.scenario_id,'scenario_id')):_identity(value,name)
        if not self.attacked_identities or len(set(self.attacked_identities))!=len(self.attacked_identities):raise ValueError('official attacked identities required')
        if any(type(x) is not str or not x for x in (*self.attacked_identities,*self.explicit_affected_processes)):raise ValueError('invalid official identity')
        _sha(self.official_source_hash,'official_source_hash');_sha(self.scenario_authority_hash,'scenario_authority_hash')


def assert_method_blind_nested_v2(value:Any,path:str='root')->None:
    if isinstance(value,Mapping):
        for key,item in value.items():
            lowered=str(key).lower()
            if any(token in lowered for token in FORBIDDEN):raise ValueError(f'METHOD_OUTCOME_TAINT:{path}.{key}')
            assert_method_blind_nested_v2(item,f'{path}.{key}')
    elif isinstance(value,(tuple,list)):
        for index,item in enumerate(value):assert_method_blind_nested_v2(item,f'{path}[{index}]')


def classify_p1_scenario_v2(scenario:OfficialScenarioMetadataV2,authority:FrozenP1MappingAuthorityV2)->dict[str,object]:
    """Outcome-blind classification bound to an exact mapping authority."""
    if type(scenario) is not OfficialScenarioMetadataV2 or type(authority) is not FrozenP1MappingAuthorityV2:raise ValueError('typed official scenario and mapping authority required')
    scenario.validate();authority.validate()
    if scenario.dataset_version!=authority.dataset_version:raise ValueError('scenario/mapping dataset version mismatch')
    assert_method_blind_nested_v2({'scenario':scenario.__dict__,'mapping':authority.document()})
    entries=[];unresolved=0
    for identity in sorted(scenario.attacked_identities):
        entry=authority.lookup(identity)
        if entry is None or entry.scope=='UNRESOLVED' or entry.mapping_state=='UNRESOLVED':
            entries.append('UNRESOLVED');unresolved+=1
        else:entries.append(entry.scope)
    if 'P1' in entries:status='P1_ELIGIBLE';reason='DIRECT_ATTACKED_IDENTITY_MAPS_TO_P1'
    elif unresolved:status='UNRESOLVED';reason='AT_LEAST_ONE_ATTACKED_IDENTITY_UNRESOLVED'
    elif 'P1' in scenario.explicit_affected_processes:status='CROSS_PROCESS_P1_RELEVANT';reason='OFFICIAL_EXPLICIT_AFFECTED_PROCESS_INCLUDES_P1'
    else:status='OUT_OF_SCOPE';reason='NO_DIRECT_OR_EXPLICIT_P1_AUTHORITY'
    body={'schema':'p1_scenario_eligibility_record_v2','dataset_version':scenario.dataset_version,'file_id':scenario.file_id,
          'scenario_id':scenario.scenario_id,'status':status,'reason':reason,'attacked_identity_count':len(scenario.attacked_identities),
          'unresolved_identity_count':unresolved,'official_source_hash':scenario.official_source_hash,
          'scenario_authority_hash':scenario.scenario_authority_hash,'mapping_authority_hash':authority.document()['self_hash'],
          'mapping_source_hash':authority.official_mapping_source_hash}
    return {**body,'self_hash':_hash(body)}


__all__=['OfficialScenarioMetadataV1','classify_p1_scenario_v1','assert_method_blind_payload_v1','STATUSES',
         'P1MappingEntryV2','FrozenP1MappingAuthorityV2','OfficialScenarioMetadataV2','classify_p1_scenario_v2',
         'assert_method_blind_nested_v2','MAPPING_STATES','MAPPING_SCOPES']
