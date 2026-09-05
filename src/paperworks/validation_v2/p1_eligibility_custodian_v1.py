"""Method-blind P1 scenario eligibility classifier, frozen before DG-05."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

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


__all__=['OfficialScenarioMetadataV1','classify_p1_scenario_v1','assert_method_blind_payload_v1','STATUSES']
