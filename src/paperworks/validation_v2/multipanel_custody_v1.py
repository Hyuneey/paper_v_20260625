"""Global all-panel prediction-before-any-label custody contracts.

The module is prospective and synthetic-testable.  It cannot read datasets;
callers must present hash-only receipts from the existing durable custody layer.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from typing import Any, Callable, Mapping, Sequence

from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER


class MultiPanelCustodyError(ValueError): pass
def _canon(value: Mapping[str,Any]) -> bytes:return json.dumps(dict(value),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _hash(value: Mapping[str,Any])->str:return sha256(_canon(value)).hexdigest()
def _sha(value: str, field: str)->None:
    if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise MultiPanelCustodyError(f'{field} must be sha256')
def _gitsha(value: str, field: str)->None:
    if type(value) is not str or len(value)!=40 or any(c not in '0123456789abcdef' for c in value):raise MultiPanelCustodyError(f'{field} must be full git sha')
def _identity(value: str, field: str)->None:
    if type(value) is not str or not value or any(ch in value for ch in ('/', '\\', ':')):raise MultiPanelCustodyError(f'invalid {field}')
def _publish_new(path: Path, payload: bytes)->str:
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(f'.{path.name}.{secrets.token_hex(12)}.tmp')
    try:
        with temporary.open('xb') as handle:
            handle.write(payload);handle.flush();os.fsync(handle.fileno())
        os.link(temporary,path)
        if os.name != 'nt':
            descriptor=os.open(path.parent,os.O_RDONLY)
            try:os.fsync(descriptor)
            finally:os.close(descriptor)
    except FileExistsError as exc:
        raise MultiPanelCustodyError('APPEND_ONLY_ARTIFACT_CONFLICT') from exc
    finally:
        if temporary.exists():temporary.unlink()
    if path.read_bytes()!=payload:raise MultiPanelCustodyError('DURABLE_REPLAY_MISMATCH')
    return sha256(payload).hexdigest()


class GlobalPredictionStateV1(str,Enum):
    ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED='ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED'
    ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED='ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED'
    PREDICTIONS_IN_PROGRESS_LABEL_LOCKED='PREDICTIONS_IN_PROGRESS_LABEL_LOCKED'
    GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED='GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED'
    LABEL_SCENARIO_LEASE_OPEN='LABEL_SCENARIO_LEASE_OPEN'
    RESULTS_COMPUTED='RESULTS_COMPUTED'


_STATE_ORDER = tuple(GlobalPredictionStateV1)


def validate_state_transition_v1(before: GlobalPredictionStateV1, after: GlobalPredictionStateV1) -> None:
    """Allow only the preregistered adjacent custody transition."""
    if type(before) is not GlobalPredictionStateV1 or type(after) is not GlobalPredictionStateV1:
        raise MultiPanelCustodyError('typed custody state required')
    if _STATE_ORDER.index(after) != _STATE_ORDER.index(before) + 1:
        raise MultiPanelCustodyError('CUSTODY_STATE_TRANSITION_SKIPPED')


@dataclass(frozen=True)
class PredictionCellReceiptV1:
    panel_id:str; file_id:str; method_id:str; method_authority_hash:str
    feature_projection_hash:str; prediction_artifact_hash:str; row_count:int
    timestamp_range_hash:str; alarm_count:int; system_error_count:int
    runtime_milliseconds:int; source_commit:str
    terminal_status:str='SUCCESS'
    def document(self)->dict[str,Any]:return dict(self.__dict__)
    def validate(self)->None:
        for field in ('panel_id','file_id','method_id','source_commit'):
            if not isinstance(getattr(self,field),str) or not getattr(self,field):raise MultiPanelCustodyError('invalid prediction identity')
        for field in ('method_authority_hash','feature_projection_hash','prediction_artifact_hash','timestamp_range_hash'):_sha(getattr(self,field),field)
        if type(self.row_count) is not int or self.row_count<=0 or any(type(getattr(self,f)) is not int or getattr(self,f)<0 for f in ('alarm_count','system_error_count','runtime_milliseconds')):raise MultiPanelCustodyError('invalid prediction census')
        if self.alarm_count>self.row_count:raise MultiPanelCustodyError('alarm count exceeds rows')
        if self.terminal_status not in ('SUCCESS','METHOD_FAILURE'):raise MultiPanelCustodyError('invalid terminal status')
        if self.terminal_status == 'METHOD_FAILURE' and self.alarm_count != 0:
            raise MultiPanelCustodyError('failure cannot be represented as alarm output')


@dataclass(frozen=True)
class GlobalPredictionManifestV1:
    expected_cells:tuple[tuple[str,str,str],...]
    receipts:tuple[PredictionCellReceiptV1,...]
    evaluation_policy_hash:str; metric_authority_hash:str; dg05_authorization_hash:str
    state:GlobalPredictionStateV1=GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED
    def document(self)->dict[str,Any]:
        body={'schema':'multipanel_global_prediction_manifest_v1','expected_cells':[list(v) for v in self.expected_cells],
              'receipts':[v.document() for v in self.receipts],'evaluation_policy_hash':self.evaluation_policy_hash,
              'metric_authority_hash':self.metric_authority_hash,'dg05_authorization_hash':self.dg05_authorization_hash,
              'state':self.state.value}
        return {**body,'self_hash':_hash(body)}
    def validate(self)->None:
        for value,name in ((self.evaluation_policy_hash,'evaluation_policy_hash'),(self.metric_authority_hash,'metric_authority_hash'),(self.dg05_authorization_hash,'dg05_authorization_hash')):_sha(value,name)
        if self.state is not GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED:raise MultiPanelCustodyError('global freeze state required')
        if not self.expected_cells or tuple(sorted(set(self.expected_cells)))!=self.expected_cells:raise MultiPanelCustodyError('expected cells must be exact sorted unique authority')
        for item in self.receipts:item.validate()
        actual=tuple(sorted((r.panel_id,r.file_id,r.method_id) for r in self.receipts))
        if actual!=self.expected_cells:raise MultiPanelCustodyError('GLOBAL_PREDICTION_CELL_CENSUS_INCOMPLETE')
        if len({(r.panel_id,r.file_id,r.prediction_artifact_hash) for r in self.receipts})!=len(self.receipts):raise MultiPanelCustodyError('prediction receipt alias')


class LabelScenarioLeaseV1:
    __slots__=('__token','manifest_hash','used')
    def __init__(self,manifest_hash:str):self.__token=secrets.token_hex(32);self.manifest_hash=manifest_hash;self.used=False
    def __repr__(self)->str:return 'LabelScenarioLeaseV1(<opaque>)'


def issue_label_scenario_lease_v1(manifest:GlobalPredictionManifestV1)->LabelScenarioLeaseV1:
    if type(manifest) is not GlobalPredictionManifestV1:raise MultiPanelCustodyError('typed manifest required')
    manifest.validate();return LabelScenarioLeaseV1(manifest.document()['self_hash'])


def consume_label_scenario_lease_v1(lease:LabelScenarioLeaseV1,manifest:GlobalPredictionManifestV1,reader):
    if type(lease) is not LabelScenarioLeaseV1 or lease.used:raise MultiPanelCustodyError('invalid or consumed label lease')
    manifest.validate()
    if manifest.document()['self_hash']!=lease.manifest_hash:raise MultiPanelCustodyError('manifest mutated before label access')
    if not callable(reader):raise MultiPanelCustodyError('label reader must be callable')
    lease.used=True;return reader()


def validate_attack_feature_projection_contract_v1(document:Mapping[str,Any])->None:
    required={'panel_id','file_id','timestamp_id','approved_feature_ids','projection_hash','row_count','label_values_parsed','scenario_values_parsed'}
    if set(document)!=required or document['label_values_parsed'] is not False or document['scenario_values_parsed'] is not False:raise MultiPanelCustodyError('feature projection contract tainted')
    if not document['approved_feature_ids'] or any(not x.startswith('P1_') for x in document['approved_feature_ids']):raise MultiPanelCustodyError('positive feature allowlist required')
    _sha(document['projection_hash'],'projection_hash')


def project_attack_columns_v1(*, header: Sequence[str], column_readers: Mapping[str, Any],
                              timestamp_id: str, approved_feature_ids: Sequence[str]) -> dict[str, tuple[Any, ...]]:
    """Positive-allowlist projection; excluded column readers are never invoked."""
    if not header or len(set(header)) != len(header) or set(column_readers) != set(header):
        raise MultiPanelCustodyError('invalid attack container schema')
    selected=(timestamp_id,*tuple(approved_feature_ids))
    if len(selected) != len(set(selected)) or any(name not in header for name in selected):
        raise MultiPanelCustodyError('unresolved positive allowlist')
    if not approved_feature_ids or any(not name.startswith('P1_') for name in approved_feature_ids):
        raise MultiPanelCustodyError('positive feature allowlist required')
    values={name:tuple(column_readers[name]()) for name in selected}
    lengths={len(value) for value in values.values()}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) <= 0:
        raise MultiPanelCustodyError('projection row mismatch')
    return values


# V2 is the authoritative pre-DG05 contract.  V1 remains importable only for
# compatibility with the already-frozen preparation history.
FROZEN_PANEL_ORDER_V2=(
    'HAI23_TEST2_PRIMARY_HELDOUT_V1',
    'HAI22_EXTERNAL_REPLICATION_V1',
    'HAI21_EXTERNAL_REPLICATION_V1',
)
PRIMARY_METHODS_V2=('M0_PCA_SPE','M1_T0_RULE_ONLY','M2_T2_RULE_ONLY','M3_PCA_PLUS_T0','M4_PCA_PLUS_T2')
SECONDARY_METHODS_V2={
    FROZEN_PANEL_ORDER_V2[0]:('ISOLATION_FOREST','ISOLATION_FOREST_PLUS_T2','V2A_RULE_ONLY_REFERENCE','HISTORICAL_PCA_PLUS_V2A_CONTINUITY'),
    FROZEN_PANEL_ORDER_V2[1]:('ISOLATION_FOREST','ISOLATION_FOREST_PLUS_T2'),
    FROZEN_PANEL_ORDER_V2[2]:('ISOLATION_FOREST','ISOLATION_FOREST_PLUS_T2'),
}
FROZEN_METHOD_BUNDLE_HASH_V2='dab320da47489e5093862b7c4675523c3e6b710faceb753e7f39c8e56f002fe2'
FROZEN_ATTACK_FILE_CENSUS_HASH_V2='5018ba8d01e32a8a2ff4cf95cdb6ca75b51b006b812acf5cffe2b1d26b8a6a16'
FROZEN_AUTHORITY_SOURCE_COMMIT_V2='fe4f42c4d40000ab369b5de0e5b0f5e748020dab'
FROZEN_METRIC_AUTHORITY_HASH_V2='fda07178f1fa8b5b889c4043e33ee9934b99dfbf282e31cca5ae9fcc2a461dbb'
FROZEN_P1_CUSTODIAN_AUTHORITY_HASH_V2='a1c5f1ac8bde9a54e21d29c261f33e876fbd4fe84e9aa92ffd36eb0968570ea0'
FROZEN_DATASET_VERSIONS_V2={
    FROZEN_PANEL_ORDER_V2[0]:'23.05',FROZEN_PANEL_ORDER_V2[1]:'22.04',FROZEN_PANEL_ORDER_V2[2]:'21.03',
}
FROZEN_TIMESTAMP_IDS_V2={
    FROZEN_PANEL_ORDER_V2[0]:'timestamp',FROZEN_PANEL_ORDER_V2[1]:'timestamp',FROZEN_PANEL_ORDER_V2[2]:'time',
}
FROZEN_FEATURE_IDS_V2={
    FROZEN_PANEL_ORDER_V2[0]:tuple(P1_FEATURE_ORDER),
    FROZEN_PANEL_ORDER_V2[1]:(
        'P1_FCV01D','P1_FCV01Z','P1_FCV02D','P1_FCV02Z','P1_FCV03D','P1_FCV03Z',
        'P1_LCV01D','P1_LCV01Z','P1_PCV01D','P1_PCV01Z','P1_PCV02Z','P1_PP04',
        'P1_FT01','P1_FT01Z','P1_FT02','P1_FT02Z','P1_FT03','P1_FT03Z',
        'P1_LIT01','P1_PIT01','P1_PIT02','P1_TIT01','P1_TIT02','P1_TIT03',
    ),
    FROZEN_PANEL_ORDER_V2[2]:(
        'P1_FCV01D','P1_FCV01Z','P1_FCV02D','P1_FCV02Z','P1_FCV03D','P1_FCV03Z',
        'P1_LCV01D','P1_LCV01Z','P1_PCV01D','P1_PCV01Z','P1_PCV02Z',
        'P1_FT01','P1_FT01Z','P1_FT02','P1_FT02Z','P1_FT03','P1_FT03Z',
        'P1_LIT01','P1_PIT01','P1_PIT02','P1_TIT01','P1_TIT02',
    ),
}
FROZEN_ATTACK_FILE_IDS_V2={
    FROZEN_PANEL_ORDER_V2[0]:('hai-test2.csv',),
    FROZEN_PANEL_ORDER_V2[1]:('test1.csv','test2.csv','test3.csv','test4.csv'),
    FROZEN_PANEL_ORDER_V2[2]:('test1.csv','test2.csv','test3.csv','test4.csv','test5.csv'),
}
FROZEN_DETECTOR_AUTHORITY_HASHES_V2={
    FROZEN_PANEL_ORDER_V2[0]:'1234517f244f45ed5a9b6e7b555138773f67891e28c27dd28404b1d71c959e2d',
    FROZEN_PANEL_ORDER_V2[1]:'3abe6aeb898e8ea0bbca9eb41bab968d6a53232aee3c70a3fc5885008ffe67c4',
    FROZEN_PANEL_ORDER_V2[2]:'0eb58f17096d5ca0d5bbbc4c9d51a7220dc45d19830e00671a0fbfaee78315d6',
}
FROZEN_PORTFOLIO_HASHES_V2={
    FROZEN_PANEL_ORDER_V2[0]:{'T0':'d95c0bb8234304f2b769e088f4399b6c071b2156982c9e1fadd175dbab5dba02','T2':'bc2b5996989228f198dbcbf38cbedaf38516366f55d5011978ecda94ccf699b6','V2A':'ec0b3e2a32d457287cb8b101bec39059e99335be3fd85a3d1fb98668224c52aa'},
    FROZEN_PANEL_ORDER_V2[1]:{'T0':'94f130408361e6b4a8051ed4a72a0ad385e90cb3212e2bf0d27af300f481503f','T2':'b58313cd142256d000f89fd4a40512763b35e6b50752229109646bafc243fb5c'},
    FROZEN_PANEL_ORDER_V2[2]:{'T0':'f9cad3c00c422614012b2147f3c21951632f8738ce2d8f9f1108d61ae69d6ef3','T2':'9815c9a66debed593e21364377113d18422a840389d306a4a7648d5f035599dc'},
}
FROZEN_FUSION_POLICY_HASH_V2='587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc'


def _composite_method_hash_v2(panel_id:str,method_id:str,*components:str)->str:
    return _hash({'schema':'multipanel_composite_method_authority_v2','panel_id':panel_id,
                  'method_id':method_id,'component_authority_hashes':list(components)})


def frozen_method_cell_authorities_v2(panel_id:str)->tuple['MethodCellAuthorityV2',...]:
    """Derive every cell from the immutable detector/portfolio/Fusion roots."""
    if panel_id not in FROZEN_PANEL_ORDER_V2:raise MultiPanelCustodyError('unknown frozen panel')
    detector=FROZEN_DETECTOR_AUTHORITY_HASHES_V2[panel_id];portfolios=FROZEN_PORTFOLIO_HASHES_V2[panel_id]
    component_map={
        'M0_PCA_SPE':(detector,),
        'M1_T0_RULE_ONLY':(portfolios['T0'],),
        'M2_T2_RULE_ONLY':(portfolios['T2'],),
        'M3_PCA_PLUS_T0':(detector,portfolios['T0'],FROZEN_FUSION_POLICY_HASH_V2),
        'M4_PCA_PLUS_T2':(detector,portfolios['T2'],FROZEN_FUSION_POLICY_HASH_V2),
        'ISOLATION_FOREST':(detector,),
        'ISOLATION_FOREST_PLUS_T2':(detector,portfolios['T2'],FROZEN_FUSION_POLICY_HASH_V2),
    }
    if panel_id==FROZEN_PANEL_ORDER_V2[0]:
        component_map.update({
            'V2A_RULE_ONLY_REFERENCE':(portfolios['V2A'],),
            'HISTORICAL_PCA_PLUS_V2A_CONTINUITY':(detector,portfolios['V2A'],FROZEN_FUSION_POLICY_HASH_V2),
        })
    result=[]
    for method_id in PRIMARY_METHODS_V2+SECONDARY_METHODS_V2[panel_id]:
        components=component_map[method_id]
        method_hash=components[0] if len(components)==1 else _composite_method_hash_v2(panel_id,method_id,*components)
        execution_hash=_hash({'schema':'multipanel_method_execution_authority_v2','panel_id':panel_id,
                              'method_id':method_id,'method_authority_hash':method_hash,
                              'method_bundle_hash':FROZEN_METHOD_BUNDLE_HASH_V2,'components':list(components)})
        result.append(MethodCellAuthorityV2(method_id,method_hash,execution_hash))
    return tuple(result)


@dataclass(frozen=True)
class FrozenFeatureAllowlistAuthorityV2:
    panel_id:str; dataset_version:str; timestamp_id:str; feature_ids:tuple[str,...]
    method_bundle_hash:str; source_commit:str
    def body(self)->dict[str,Any]:
        return {'schema':'multipanel_feature_allowlist_authority_v2','panel_id':self.panel_id,
                'dataset_version':self.dataset_version,'timestamp_id':self.timestamp_id,
                'feature_ids':list(self.feature_ids),'method_bundle_hash':self.method_bundle_hash,
                'source_commit':self.source_commit}
    def document(self)->dict[str,Any]:
        body=self.body();return {**body,'self_hash':_hash(body)}
    def validate(self)->None:
        if self.panel_id not in FROZEN_PANEL_ORDER_V2:raise MultiPanelCustodyError('unknown frozen panel')
        if (self.dataset_version,self.timestamp_id,self.feature_ids)!=(FROZEN_DATASET_VERSIONS_V2[self.panel_id],FROZEN_TIMESTAMP_IDS_V2[self.panel_id],FROZEN_FEATURE_IDS_V2[self.panel_id]):
            raise MultiPanelCustodyError('allowlist differs from frozen panel authority')
        if self.method_bundle_hash!=FROZEN_METHOD_BUNDLE_HASH_V2:raise MultiPanelCustodyError('frozen method bundle mismatch')
        if self.source_commit!=FROZEN_AUTHORITY_SOURCE_COMMIT_V2:raise MultiPanelCustodyError('allowlist source commit differs from frozen authority')


def frozen_feature_allowlist_authorities_v2()->dict[str,FrozenFeatureAllowlistAuthorityV2]:
    """Return the only feature-allowlist authorities admissible to DG-05 custody."""
    return {panel:FrozenFeatureAllowlistAuthorityV2(panel,FROZEN_DATASET_VERSIONS_V2[panel],
            FROZEN_TIMESTAMP_IDS_V2[panel],FROZEN_FEATURE_IDS_V2[panel],FROZEN_METHOD_BUNDLE_HASH_V2,
            FROZEN_AUTHORITY_SOURCE_COMMIT_V2) for panel in FROZEN_PANEL_ORDER_V2}


@dataclass(frozen=True,order=True)
class PhysicalFileIdentityV2:
    panel_id:str; file_id:str; raw_container_hash:str; header_hash:str; official_source_hash:str
    def validate(self)->None:
        if self.panel_id not in FROZEN_PANEL_ORDER_V2:raise MultiPanelCustodyError('unknown physical file panel')
        _identity(self.file_id,'file_id')
        for name in ('raw_container_hash','header_hash','official_source_hash'):_sha(getattr(self,name),name)
    def document(self)->dict[str,str]:return dict(self.__dict__)


@dataclass(frozen=True)
class FrozenPhysicalFileAuthorityV2:
    files:tuple[PhysicalFileIdentityV2,...]; attack_file_census_authority_hash:str
    dg05_authorization_hash:str; source_commit:str
    def body(self)->dict[str,Any]:
        return {'schema':'multipanel_physical_attack_file_authority_v2','files':[item.document() for item in self.files],
                'attack_file_census_authority_hash':self.attack_file_census_authority_hash,
                'dg05_authorization_hash':self.dg05_authorization_hash,'source_commit':self.source_commit}
    def document(self)->dict[str,Any]:
        body=self.body();return {**body,'self_hash':_hash(body)}
    def validate(self)->None:
        expected=tuple(sorted(self.files,key=lambda item:(FROZEN_PANEL_ORDER_V2.index(item.panel_id),item.file_id))) if self.files else ()
        if not self.files or expected!=self.files or len({(v.panel_id,v.file_id) for v in self.files})!=len(self.files):
            raise MultiPanelCustodyError('canonical exact physical file authority required')
        if {item.panel_id for item in self.files}!=set(FROZEN_PANEL_ORDER_V2):raise MultiPanelCustodyError('all frozen panels required')
        for item in self.files:item.validate()
        by_panel={panel:tuple(item.file_id for item in self.files if item.panel_id==panel) for panel in FROZEN_PANEL_ORDER_V2}
        if by_panel!=FROZEN_ATTACK_FILE_IDS_V2:raise MultiPanelCustodyError('physical files differ from frozen public census')
        if self.attack_file_census_authority_hash!=FROZEN_ATTACK_FILE_CENSUS_HASH_V2:raise MultiPanelCustodyError('attack file census authority mismatch')
        _sha(self.dg05_authorization_hash,'dg05_authorization_hash')
        if self.source_commit!=FROZEN_AUTHORITY_SOURCE_COMMIT_V2:raise MultiPanelCustodyError('physical authority source commit mismatch')
    def lookup(self,panel_id:str,file_id:str)->PhysicalFileIdentityV2:
        self.validate()
        for item in self.files:
            if (item.panel_id,item.file_id)==(panel_id,file_id):return item
        raise MultiPanelCustodyError('file absent from frozen physical authority')


@dataclass(frozen=True)
class AttackFeatureProjectionReceiptV2:
    panel_id:str; file_id:str; timestamp_id:str; approved_feature_ids:tuple[str,...]
    feature_allowlist_authority_hash:str; raw_container_hash:str; header_hash:str
    projection_hash:str; row_count:int; timestamp_range_hash:str; source_commit:str
    label_values_parsed:bool=False; label_values_decoded:bool=False; label_values_inspected:bool=False
    label_values_counted:bool=False; label_values_validated:bool=False; label_values_filtered_on:bool=False
    label_values_used:bool=False; scenario_values_parsed:bool=False; scenario_values_decoded:bool=False
    scenario_values_inspected:bool=False; scenario_values_counted:bool=False; scenario_values_validated:bool=False
    scenario_values_filtered_on:bool=False; scenario_values_used:bool=False
    def document(self)->dict[str,Any]:
        body={'schema':'multipanel_attack_feature_projection_receipt_v2',**self.__dict__}
        body['approved_feature_ids']=list(self.approved_feature_ids)
        return {**body,'self_hash':_hash(body)}
    def validate(self,authority:FrozenFeatureAllowlistAuthorityV2,physical:FrozenPhysicalFileAuthorityV2|None=None)->None:
        if type(authority) is not FrozenFeatureAllowlistAuthorityV2:raise MultiPanelCustodyError('typed allowlist authority required')
        authority.validate()
        if (self.panel_id,self.timestamp_id,self.approved_feature_ids)!=(authority.panel_id,authority.timestamp_id,authority.feature_ids):
            raise MultiPanelCustodyError('projection is not bound to exact allowlist')
        if self.feature_allowlist_authority_hash!=authority.document()['self_hash']:raise MultiPanelCustodyError('allowlist authority hash mismatch')
        _identity(self.file_id,'file_id')
        if self.source_commit!=FROZEN_AUTHORITY_SOURCE_COMMIT_V2:raise MultiPanelCustodyError('projection source commit mismatch')
        for name in ('feature_allowlist_authority_hash','raw_container_hash','header_hash','projection_hash','timestamp_range_hash'):_sha(getattr(self,name),name)
        if type(self.row_count) is not int or self.row_count<=0:raise MultiPanelCustodyError('invalid projection row count')
        flags=(self.label_values_parsed,self.label_values_decoded,self.label_values_inspected,self.label_values_counted,
               self.label_values_validated,self.label_values_filtered_on,self.label_values_used,self.scenario_values_parsed,
               self.scenario_values_decoded,self.scenario_values_inspected,self.scenario_values_counted,
               self.scenario_values_validated,self.scenario_values_filtered_on,self.scenario_values_used)
        if any(type(v) is not bool or v for v in flags):raise MultiPanelCustodyError('excluded label/scenario value contact')
        if physical is not None:
            item=physical.lookup(self.panel_id,self.file_id)
            if (self.raw_container_hash,self.header_hash)!=(item.raw_container_hash,item.header_hash):raise MultiPanelCustodyError('projection/physical file authority mismatch')


@dataclass(frozen=True)
class MethodCellAuthorityV2:
    method_id:str; method_authority_hash:str; execution_authority_hash:str
    def validate(self,panel_id:str)->None:
        _identity(self.method_id,'method_id');_sha(self.method_authority_hash,'method_authority_hash');_sha(self.execution_authority_hash,'execution_authority_hash')
        expected=next((item for item in frozen_method_cell_authorities_v2(panel_id) if item.method_id==self.method_id),None)
        if expected is None or self!=expected:raise MultiPanelCustodyError('method cell differs from frozen component authorities')
    def document(self)->dict[str,str]:return dict(self.__dict__)


@dataclass(frozen=True)
class GlobalCellCensusAuthorityV2:
    files_by_panel:tuple[tuple[str,tuple[str,...]],...]
    methods_by_panel:tuple[tuple[str,tuple[MethodCellAuthorityV2,...]],...]
    method_bundle_hash:str; physical_file_authority_hash:str
    allowlist_authority_hashes:tuple[tuple[str,str],...]; source_commit:str
    def validate(self)->None:
        if tuple(panel for panel,_ in self.files_by_panel)!=FROZEN_PANEL_ORDER_V2 or tuple(panel for panel,_ in self.methods_by_panel)!=FROZEN_PANEL_ORDER_V2:
            raise MultiPanelCustodyError('exact frozen panel order required')
        for panel,files in self.files_by_panel:
            if files!=FROZEN_ATTACK_FILE_IDS_V2[panel] or len(set(files))!=len(files):raise MultiPanelCustodyError('exact physical file census required')
            for value in files:_identity(value,'file_id')
        for panel,methods in self.methods_by_panel:
            expected=PRIMARY_METHODS_V2+SECONDARY_METHODS_V2[panel]
            if tuple(item.method_id for item in methods)!=expected:raise MultiPanelCustodyError('exact frozen method census required')
            for item in methods:item.validate(panel)
        if self.method_bundle_hash!=FROZEN_METHOD_BUNDLE_HASH_V2:raise MultiPanelCustodyError('frozen method bundle mismatch')
        expected_allowlists=tuple((panel,authority.document()['self_hash']) for panel,authority in frozen_feature_allowlist_authorities_v2().items())
        if self.allowlist_authority_hashes!=expected_allowlists:raise MultiPanelCustodyError('exact frozen allowlist authority census required')
        _sha(self.physical_file_authority_hash,'physical_file_authority_hash')
        if self.source_commit!=FROZEN_AUTHORITY_SOURCE_COMMIT_V2:raise MultiPanelCustodyError('census source commit mismatch')
    def body(self)->dict[str,Any]:
        return {'schema':'multipanel_global_cell_census_authority_v2','files_by_panel':[[p,list(v)] for p,v in self.files_by_panel],
                'methods_by_panel':[[p,[m.document() for m in v]] for p,v in self.methods_by_panel],
                'method_bundle_hash':self.method_bundle_hash,'physical_file_authority_hash':self.physical_file_authority_hash,
                'allowlist_authority_hashes':[list(v) for v in self.allowlist_authority_hashes],
                'source_commit':self.source_commit}
    def document(self)->dict[str,Any]:
        body=self.body();return {**body,'self_hash':_hash(body)}
    def expected_cells(self)->tuple[tuple[str,str,str],...]:
        self.validate();files=dict(self.files_by_panel);methods=dict(self.methods_by_panel)
        return tuple((panel,file_id,method.method_id) for panel in FROZEN_PANEL_ORDER_V2 for file_id in files[panel] for method in methods[panel])
    def method(self,panel_id:str,method_id:str)->MethodCellAuthorityV2:
        for panel,methods in self.methods_by_panel:
            if panel==panel_id:
                for item in methods:
                    if item.method_id==method_id:return item
        raise MultiPanelCustodyError('cell absent from frozen method census')


@dataclass(frozen=True)
class PredictionSuccessReceiptV2:
    panel_id:str; file_id:str; method_id:str; method_authority_hash:str; execution_authority_hash:str
    feature_projection_hash:str; prediction_artifact_hash:str; row_count:int; timestamp_range_hash:str
    alarm_count:int; runtime_milliseconds:int; source_commit:str; system_error_count:int=0
    terminal_status:str='SUCCESS'
    def document(self)->dict[str,Any]:
        body={'schema':'multipanel_prediction_success_receipt_v2',**self.__dict__};return {**body,'self_hash':_hash(body)}
    def validate(self,census:GlobalCellCensusAuthorityV2)->None:
        _validate_cell_identity_v2(self,census)
        for name in ('feature_projection_hash','prediction_artifact_hash','timestamp_range_hash'):_sha(getattr(self,name),name)
        if self.terminal_status!='SUCCESS' or self.system_error_count!=0:raise MultiPanelCustodyError('success receipt cannot report failure')
        if type(self.row_count) is not int or self.row_count<=0 or type(self.alarm_count) is not int or not 0<=self.alarm_count<=self.row_count:
            raise MultiPanelCustodyError('invalid success census')
        if type(self.runtime_milliseconds) is not int or self.runtime_milliseconds<0:raise MultiPanelCustodyError('invalid runtime')


@dataclass(frozen=True)
class PredictionFailureReceiptV2:
    panel_id:str; file_id:str; method_id:str; method_authority_hash:str; execution_authority_hash:str
    feature_projection_hash:str; row_count:int; timestamp_range_hash:str; error_class:str; error_hash:str
    system_error_count:int; runtime_milliseconds:int; source_commit:str; terminal_status:str='METHOD_FAILURE'
    def document(self)->dict[str,Any]:
        body={'schema':'multipanel_prediction_failure_receipt_v2',**self.__dict__};return {**body,'self_hash':_hash(body)}
    def validate(self,census:GlobalCellCensusAuthorityV2)->None:
        _validate_cell_identity_v2(self,census)
        for name in ('feature_projection_hash','timestamp_range_hash','error_hash'):_sha(getattr(self,name),name)
        _identity(self.error_class,'error_class')
        if self.terminal_status!='METHOD_FAILURE' or type(self.system_error_count) is not int or self.system_error_count<=0:
            raise MultiPanelCustodyError('tagged method failure required')
        if type(self.row_count) is not int or self.row_count<=0 or type(self.runtime_milliseconds) is not int or self.runtime_milliseconds<0:
            raise MultiPanelCustodyError('invalid failure census')


def _validate_cell_identity_v2(receipt:Any,census:GlobalCellCensusAuthorityV2)->None:
    census.validate();_identity(receipt.file_id,'file_id')
    if receipt.source_commit!=FROZEN_AUTHORITY_SOURCE_COMMIT_V2:raise MultiPanelCustodyError('prediction receipt source commit mismatch')
    if (receipt.panel_id,receipt.file_id,receipt.method_id) not in set(census.expected_cells()):raise MultiPanelCustodyError('cell outside frozen census')
    authority=census.method(receipt.panel_id,receipt.method_id)
    if (receipt.method_authority_hash,receipt.execution_authority_hash)!=(authority.method_authority_hash,authority.execution_authority_hash):
        raise MultiPanelCustodyError('method authority mismatch')


PredictionTerminalReceiptV2=PredictionSuccessReceiptV2|PredictionFailureReceiptV2


@dataclass(frozen=True)
class GlobalPredictionManifestV2:
    census:GlobalCellCensusAuthorityV2; projection_receipts:tuple[AttackFeatureProjectionReceiptV2,...]
    receipts:tuple[PredictionTerminalReceiptV2,...]; evaluation_policy_hash:str; metric_authority_hash:str
    p1_custodian_authority_hash:str; dg05_authorization_hash:str; source_commit:str
    state:GlobalPredictionStateV1=GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED
    def document(self)->dict[str,Any]:
        body={'schema':'multipanel_global_prediction_manifest_v2','census_authority_hash':self.census.document()['self_hash'],
              'expected_cells':[list(v) for v in self.census.expected_cells()],
              'projection_receipts':[v.document() for v in self.projection_receipts],
              'receipts':[v.document() for v in self.receipts],'evaluation_policy_hash':self.evaluation_policy_hash,
              'metric_authority_hash':self.metric_authority_hash,'p1_custodian_authority_hash':self.p1_custodian_authority_hash,
              'dg05_authorization_hash':self.dg05_authorization_hash,'source_commit':self.source_commit,'state':self.state.value}
        return {**body,'self_hash':_hash(body)}
    def validate(self,allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2],physical:FrozenPhysicalFileAuthorityV2)->None:
        self.census.validate()
        for name in ('evaluation_policy_hash','metric_authority_hash','p1_custodian_authority_hash','dg05_authorization_hash'):_sha(getattr(self,name),name)
        if self.source_commit!=FROZEN_AUTHORITY_SOURCE_COMMIT_V2:raise MultiPanelCustodyError('manifest source commit mismatch')
        if self.metric_authority_hash!=FROZEN_METRIC_AUTHORITY_HASH_V2:raise MultiPanelCustodyError('manifest metric authority mismatch')
        if self.p1_custodian_authority_hash!=FROZEN_P1_CUSTODIAN_AUTHORITY_HASH_V2:raise MultiPanelCustodyError('manifest P1 custodian authority mismatch')
        if self.state is not GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED:raise MultiPanelCustodyError('global label-locked freeze required')
        physical.validate()
        if physical.document()['self_hash']!=self.census.physical_file_authority_hash:raise MultiPanelCustodyError('physical authority hash mismatch')
        if physical.dg05_authorization_hash!=self.dg05_authorization_hash:raise MultiPanelCustodyError('physical/manifest DG05 authorization mismatch')
        if self.source_commit!=self.census.source_commit or physical.source_commit!=self.source_commit:raise MultiPanelCustodyError('source commit authority mismatch')
        files={(panel,file_id) for panel,values in self.census.files_by_panel for file_id in values}
        if files!={(item.panel_id,item.file_id) for item in physical.files}:raise MultiPanelCustodyError('physical file/census mismatch')
        projections={(item.panel_id,item.file_id):item for item in self.projection_receipts}
        if len(projections)!=len(self.projection_receipts) or set(projections)!=files:raise MultiPanelCustodyError('projection receipt census mismatch')
        expected_allowlists=dict(self.census.allowlist_authority_hashes)
        if set(allowlists)!=set(FROZEN_PANEL_ORDER_V2):raise MultiPanelCustodyError('exact allowlist authority map required')
        for (panel,_),item in projections.items():
            if panel not in allowlists:raise MultiPanelCustodyError('missing allowlist authority')
            if allowlists[panel].document()['self_hash']!=expected_allowlists[panel] or allowlists[panel].method_bundle_hash!=self.census.method_bundle_hash or allowlists[panel].source_commit!=self.source_commit:
                raise MultiPanelCustodyError('allowlist authority/census mismatch')
            item.validate(allowlists[panel],physical)
        actual=[]
        for receipt in self.receipts:
            if type(receipt) not in (PredictionSuccessReceiptV2,PredictionFailureReceiptV2):raise MultiPanelCustodyError('tagged terminal receipt required')
            receipt.validate(self.census);actual.append((receipt.panel_id,receipt.file_id,receipt.method_id))
            projection=projections[(receipt.panel_id,receipt.file_id)]
            if (receipt.feature_projection_hash,receipt.row_count,receipt.timestamp_range_hash)!=(projection.projection_hash,projection.row_count,projection.timestamp_range_hash):
                raise MultiPanelCustodyError('prediction/projection identity mismatch')
        if tuple(actual)!=self.census.expected_cells():raise MultiPanelCustodyError('GLOBAL_PREDICTION_CELL_CENSUS_INCOMPLETE_OR_OUT_OF_ORDER')


def project_attack_columns_v2(*,header:Sequence[str],column_readers:Mapping[str,Callable[[],Sequence[Any]]],
                              authority:FrozenFeatureAllowlistAuthorityV2,file_id:str,raw_container_hash:str,
                              source_commit:str)->tuple[dict[str,tuple[Any,...]],AttackFeatureProjectionReceiptV2]:
    authority.validate();_sha(raw_container_hash,'raw_container_hash');_identity(file_id,'file_id')
    if source_commit!=FROZEN_AUTHORITY_SOURCE_COMMIT_V2:raise MultiPanelCustodyError('projection source commit mismatch')
    if not header or len(set(header))!=len(header) or set(column_readers)!=set(header):raise MultiPanelCustodyError('invalid attack container schema')
    selected=(authority.timestamp_id,*authority.feature_ids)
    if any(value not in header for value in selected):raise MultiPanelCustodyError('allowlisted field absent')
    values={name:tuple(column_readers[name]()) for name in selected}
    lengths={len(value) for value in values.values()}
    if len(lengths)!=1 or next(iter(lengths),0)<=0:raise MultiPanelCustodyError('projection row mismatch')
    row_count=next(iter(lengths));projection_hash=sha256(canonical_projection_bytes_v2(values,selected)).hexdigest()
    timestamp_range_hash=sha256(_canon({'first':values[authority.timestamp_id][0],'last':values[authority.timestamp_id][-1],'rows':row_count})).hexdigest()
    header_hash=sha256(_canon({'header':list(header)})).hexdigest()
    receipt=AttackFeatureProjectionReceiptV2(authority.panel_id,file_id,authority.timestamp_id,authority.feature_ids,
        authority.document()['self_hash'],raw_container_hash,header_hash,projection_hash,row_count,timestamp_range_hash,source_commit)
    receipt.validate(authority);return values,receipt


def canonical_projection_bytes_v2(values:Mapping[str,Sequence[Any]],order:Sequence[str])->bytes:
    if set(values)!=set(order):raise MultiPanelCustodyError('projection contains non-allowlisted field')
    return _canon({'columns':list(order),'values':[list(values[name]) for name in order]})


def replay_projection_artifact_v2(path:Path,receipt:AttackFeatureProjectionReceiptV2)->bool:
    payload=path.read_bytes()
    if sha256(payload).hexdigest()!=receipt.projection_hash:return False
    try:value=json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError,json.JSONDecodeError):return False
    if type(value) is not dict or set(value)!= {'columns','values'}:return False
    expected_columns=[receipt.timestamp_id,*receipt.approved_feature_ids]
    if value.get('columns')!=expected_columns:return False
    vectors=value.get('values')
    return (isinstance(vectors,list) and len(vectors)==len(expected_columns)
            and all(isinstance(vector,list) and len(vector)==receipt.row_count for vector in vectors))


def persist_global_manifest_v2(directory:Path,manifest:GlobalPredictionManifestV2,
                               allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2],physical:FrozenPhysicalFileAuthorityV2,
                               projection_artifacts:Mapping[tuple[str,str],Path],
                               prediction_artifacts:Mapping[tuple[str,str,str],Path])->dict[str,Any]:
    manifest.validate(allowlists,physical)
    projections={(r.panel_id,r.file_id):r for r in manifest.projection_receipts}
    if set(projection_artifacts)!=set(projections):raise MultiPanelCustodyError('projection artifact census mismatch')
    for cell,path in projection_artifacts.items():
        if not path.is_file() or not replay_projection_artifact_v2(path,projections[cell]):
            raise MultiPanelCustodyError('projection artifact replay mismatch')
    success={(r.panel_id,r.file_id,r.method_id):r for r in manifest.receipts if type(r) is PredictionSuccessReceiptV2}
    if set(prediction_artifacts)!=set(success):raise MultiPanelCustodyError('success artifact census mismatch')
    for cell,path in prediction_artifacts.items():
        if not path.is_file() or replay_prediction_artifact_v2(path,success[cell]) is False:
            raise MultiPanelCustodyError('prediction artifact replay mismatch')
    body=manifest.document();payload=canonical_json_line_v2(body)
    manifest_path=directory/'global_prediction_manifest_v2.json';file_hash=_publish_new(manifest_path,payload)
    prediction_records=[]
    for cell,path in prediction_artifacts.items():
        try:relative=path.resolve().relative_to(directory.resolve()).as_posix()
        except ValueError as exc:raise MultiPanelCustodyError('prediction artifact outside custody directory') from exc
        prediction_records.append({'panel_id':cell[0],'file_id':cell[1],'method_id':cell[2],
                                   'artifact_relative_path':relative,'artifact_file_hash':sha256(path.read_bytes()).hexdigest()})
    freeze={'schema':'multipanel_global_prediction_manifest_freeze_receipt_v2','manifest_self_hash':body['self_hash'],
            'manifest_file_hash':file_hash,'census_authority_hash':manifest.census.document()['self_hash'],
            'physical_file_authority_hash':physical.document()['self_hash'],'projection_artifact_count':len(projection_artifacts),
            'prediction_artifact_count':len(prediction_artifacts),
            'projection_receipt_hashes':[item.document()['self_hash'] for item in manifest.projection_receipts],
            'terminal_receipt_hashes':[item.document()['self_hash'] for item in manifest.receipts],
            'prediction_records':prediction_records,'state':manifest.state.value,'source_commit':manifest.source_commit}
    freeze={**freeze,'self_hash':_hash(freeze)};_publish_new(directory/'global_prediction_manifest_v2.freeze.json',canonical_json_line_v2(freeze))
    return freeze


def canonical_json_line_v2(value:Mapping[str,Any])->bytes:return _canon(value)+b'\n'


def initialize_state_chain_v2(directory:Path,*,census_authority:GlobalCellCensusAuthorityV2,
                              physical_authority:FrozenPhysicalFileAuthorityV2,
                              allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2],evaluation_policy_hash:str,
                              metric_authority_hash:str,p1_custodian_authority_hash:str,dg05_authorization_hash:str,
                              source_commit:str)->dict[str,Any]:
    if type(census_authority) is not GlobalCellCensusAuthorityV2:raise MultiPanelCustodyError('typed exact census authority required')
    if type(physical_authority) is not FrozenPhysicalFileAuthorityV2:raise MultiPanelCustodyError('typed exact physical authority required')
    census_authority.validate();physical_authority.validate();census_authority_hash=census_authority.document()['self_hash']
    if set(allowlists)!=set(FROZEN_PANEL_ORDER_V2):raise MultiPanelCustodyError('exact allowlist authority map required')
    for panel,authority in allowlists.items():
        authority.validate()
        if authority.document()['self_hash']!=dict(census_authority.allowlist_authority_hashes)[panel]:
            raise MultiPanelCustodyError('state-chain allowlist authority mismatch')
    if physical_authority.document()['self_hash']!=census_authority.physical_file_authority_hash:
        raise MultiPanelCustodyError('state-chain physical authority mismatch')
    if physical_authority.dg05_authorization_hash!=dg05_authorization_hash:
        raise MultiPanelCustodyError('state-chain DG05 authority mismatch')
    for name,value in (('evaluation_policy_hash',evaluation_policy_hash),('metric_authority_hash',metric_authority_hash),
                       ('p1_custodian_authority_hash',p1_custodian_authority_hash),('dg05_authorization_hash',dg05_authorization_hash)):_sha(value,name)
    if source_commit!=FROZEN_AUTHORITY_SOURCE_COMMIT_V2:raise MultiPanelCustodyError('state-chain source commit mismatch')
    if metric_authority_hash!=FROZEN_METRIC_AUTHORITY_HASH_V2:raise MultiPanelCustodyError('state-chain metric authority mismatch')
    if p1_custodian_authority_hash!=FROZEN_P1_CUSTODIAN_AUTHORITY_HASH_V2:raise MultiPanelCustodyError('state-chain P1 authority mismatch')
    body={'schema':'multipanel_global_custody_transition_v2','sequence':0,'state':_STATE_ORDER[0].value,
          'predecessor_receipt_hash':None,'census_authority_hash':census_authority_hash,
          'evaluation_policy_hash':evaluation_policy_hash,'metric_authority_hash':metric_authority_hash,
          'p1_custodian_authority_hash':p1_custodian_authority_hash,'dg05_authorization_hash':dg05_authorization_hash,
          'source_commit':source_commit}
    _publish_new(directory/'physical-file-authority-v2.json',canonical_json_line_v2(physical_authority.document()))
    _publish_new(directory/'global-cell-census-authority-v2.json',canonical_json_line_v2(census_authority.document()))
    body={**body,'self_hash':_hash(body)};_publish_new(directory/'custody-transition-000.json',canonical_json_line_v2(body));return body


_TRANSITION_EVIDENCE_V2={
    GlobalPredictionStateV1.ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED:
        ('FEATURE_PROJECTION_CENSUS_FREEZE','feature-projection-census.freeze.json','multipanel_feature_projection_census_freeze_v2'),
    GlobalPredictionStateV1.PREDICTIONS_IN_PROGRESS_LABEL_LOCKED:
        ('PREDICTION_EXECUTION_START_RECEIPT','prediction-execution-start.json','multipanel_prediction_execution_start_receipt_v2'),
    GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED:
        ('GLOBAL_MANIFEST_FREEZE','global_prediction_manifest_v2.freeze.json','multipanel_global_prediction_manifest_freeze_receipt_v2'),
    GlobalPredictionStateV1.LABEL_SCENARIO_LEASE_OPEN:
        ('LABEL_SCENARIO_LEASE_ISSUE','label-scenario-lease.issue.json','multipanel_label_scenario_lease_issue_v2'),
    GlobalPredictionStateV1.RESULTS_COMPUTED:
        ('RESULT_INTEGRITY_RECEIPT','result-integrity.receipt.json','multipanel_result_integrity_receipt_v2'),
}

_TRANSITION_EVIDENCE_KEYS_V2={
    GlobalPredictionStateV1.ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED:{
        'schema','census_authority_hash','projection_artifact_count','projection_records','source_commit','self_hash'},
    GlobalPredictionStateV1.PREDICTIONS_IN_PROGRESS_LABEL_LOCKED:{
        'schema','projection_transition_hash','census_authority_hash','projection_census_hash','source_commit','self_hash'},
    GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED:{
        'schema','manifest_self_hash','manifest_file_hash','census_authority_hash','physical_file_authority_hash',
        'projection_artifact_count','prediction_artifact_count','projection_receipt_hashes','terminal_receipt_hashes',
        'prediction_records','state','source_commit','self_hash'},
    GlobalPredictionStateV1.LABEL_SCENARIO_LEASE_OPEN:{
        'schema','manifest_hash','manifest_file_hash','transition_receipt_hash','census_authority_hash',
        'evaluation_policy_hash','metric_authority_hash','p1_custodian_authority_hash','dg05_authorization_hash',
        'token_hash','source_commit','self_hash'},
    GlobalPredictionStateV1.RESULTS_COMPUTED:{
        'schema','lease_completion_receipt_hash','lease_open_transition_hash','manifest_hash',
        'result_bundle_self_hash','result_bundle_file_hash','result_record_count','source_commit','self_hash'},
}


def _read_canonical_self_hashed_v2(path:Path,schema:str)->dict[str,Any]:
    if not path.is_file():raise MultiPanelCustodyError(f'{schema} missing')
    try:value=json.loads(path.read_text(encoding='utf-8'))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise MultiPanelCustodyError(f'{schema} invalid') from exc
    if (type(value) is not dict or value.get('schema')!=schema
            or value.get('self_hash')!=_hash({k:v for k,v in value.items() if k!='self_hash'})
            or path.read_bytes()!=canonical_json_line_v2(value)):
        raise MultiPanelCustodyError(f'{schema} replay mismatch')
    return value


def _physical_from_document_v2(value:Mapping[str,Any])->FrozenPhysicalFileAuthorityV2:
    exact={'schema','files','attack_file_census_authority_hash','dg05_authorization_hash','source_commit','self_hash'}
    if set(value)!=exact or type(value.get('files')) is not list:raise MultiPanelCustodyError('physical authority fields mismatch')
    authority=FrozenPhysicalFileAuthorityV2(tuple(PhysicalFileIdentityV2(**item) for item in value['files']),
        value['attack_file_census_authority_hash'],value['dg05_authorization_hash'],value['source_commit'])
    authority.validate()
    if authority.document()!=dict(value):raise MultiPanelCustodyError('physical authority typed replay mismatch')
    return authority


def _census_from_document_v2(value:Mapping[str,Any])->GlobalCellCensusAuthorityV2:
    exact={'schema','files_by_panel','methods_by_panel','method_bundle_hash','physical_file_authority_hash',
           'allowlist_authority_hashes','source_commit','self_hash'}
    if set(value)!=exact:raise MultiPanelCustodyError('census authority fields mismatch')
    authority=GlobalCellCensusAuthorityV2(
        tuple((panel,tuple(files)) for panel,files in value['files_by_panel']),
        tuple((panel,tuple(MethodCellAuthorityV2(**item) for item in methods)) for panel,methods in value['methods_by_panel']),
        value['method_bundle_hash'],value['physical_file_authority_hash'],
        tuple((panel,authority_hash) for panel,authority_hash in value['allowlist_authority_hashes']),value['source_commit'])
    authority.validate()
    if authority.document()!=dict(value):raise MultiPanelCustodyError('census authority typed replay mismatch')
    return authority


def _projection_from_document_v2(value:Mapping[str,Any])->AttackFeatureProjectionReceiptV2:
    exact={'schema','panel_id','file_id','timestamp_id','approved_feature_ids','feature_allowlist_authority_hash',
           'raw_container_hash','header_hash','projection_hash','row_count','timestamp_range_hash','source_commit',
           'label_values_parsed','label_values_decoded','label_values_inspected','label_values_counted',
           'label_values_validated','label_values_filtered_on','label_values_used','scenario_values_parsed',
           'scenario_values_decoded','scenario_values_inspected','scenario_values_counted','scenario_values_validated',
           'scenario_values_filtered_on','scenario_values_used','self_hash'}
    if set(value)!=exact:raise MultiPanelCustodyError('projection receipt fields mismatch')
    kwargs={key:item for key,item in value.items() if key not in ('schema','self_hash')}
    kwargs['approved_feature_ids']=tuple(kwargs['approved_feature_ids'])
    receipt=AttackFeatureProjectionReceiptV2(**kwargs)
    if receipt.document()!=dict(value):raise MultiPanelCustodyError('projection receipt typed replay mismatch')
    return receipt


def _manifest_from_document_v2(value:Mapping[str,Any],census:GlobalCellCensusAuthorityV2)->GlobalPredictionManifestV2:
    exact={'schema','census_authority_hash','expected_cells','projection_receipts','receipts','evaluation_policy_hash',
           'metric_authority_hash','p1_custodian_authority_hash','dg05_authorization_hash','source_commit','state','self_hash'}
    if set(value)!=exact or value.get('census_authority_hash')!=census.document()['self_hash']:
        raise MultiPanelCustodyError('manifest authority fields mismatch')
    projections=tuple(_projection_from_document_v2(item) for item in value['projection_receipts'])
    receipts=[]
    for item in value['receipts']:
        if item.get('schema')=='multipanel_prediction_success_receipt_v2':kind=PredictionSuccessReceiptV2
        elif item.get('schema')=='multipanel_prediction_failure_receipt_v2':kind=PredictionFailureReceiptV2
        else:raise MultiPanelCustodyError('unknown terminal receipt schema')
        kwargs={key:entry for key,entry in item.items() if key not in ('schema','self_hash')};receipt=kind(**kwargs)
        if receipt.document()!=item:raise MultiPanelCustodyError('terminal receipt typed replay mismatch')
        receipts.append(receipt)
    manifest=GlobalPredictionManifestV2(census,projections,tuple(receipts),value['evaluation_policy_hash'],
        value['metric_authority_hash'],value['p1_custodian_authority_hash'],value['dg05_authorization_hash'],
        value['source_commit'],GlobalPredictionStateV1(value['state']))
    if manifest.document()!=dict(value):raise MultiPanelCustodyError('manifest typed replay mismatch')
    return manifest


def persist_projection_census_v2(directory:Path,*,census:GlobalCellCensusAuthorityV2,
                                  allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2],
                                  physical:FrozenPhysicalFileAuthorityV2,
                                  receipts:Sequence[AttackFeatureProjectionReceiptV2],
                                  projection_artifacts:Mapping[tuple[str,str],Path])->dict[str,Any]:
    """Freeze and replay every feature-only projection before prediction may start."""
    census.validate();physical.validate()
    expected=tuple((panel,file_id) for panel,files in census.files_by_panel for file_id in files)
    by_cell={(item.panel_id,item.file_id):item for item in receipts}
    if tuple(by_cell)!=expected or set(projection_artifacts)!=set(expected):raise MultiPanelCustodyError('exact projection census required')
    records=[]
    for cell in expected:
        receipt=by_cell[cell];receipt.validate(allowlists[cell[0]],physical)
        path=projection_artifacts[cell]
        try:relative=path.resolve().relative_to(directory.resolve()).as_posix()
        except ValueError as exc:raise MultiPanelCustodyError('projection artifact outside custody directory') from exc
        if not path.is_file() or not replay_projection_artifact_v2(path,receipt):raise MultiPanelCustodyError('projection artifact replay mismatch')
        records.append({'panel_id':cell[0],'file_id':cell[1],'receipt':receipt.document(),
                        'artifact_relative_path':relative,'artifact_file_hash':sha256(path.read_bytes()).hexdigest()})
    body={'schema':'multipanel_feature_projection_census_freeze_v2','census_authority_hash':census.document()['self_hash'],
          'projection_artifact_count':len(records),'projection_records':records,'source_commit':census.source_commit}
    body={**body,'self_hash':_hash(body)}
    _publish_new(directory/'feature-projection-census.freeze.json',canonical_json_line_v2(body));return body


def _validate_transition_evidence_v2(directory:Path,current:Mapping[str,Any],after:GlobalPredictionStateV1,
                                     evidence_kind:str,evidence_hash:str,evidence_path:Path)->dict[str,Any]:
    required_kind,required_name,required_schema=_TRANSITION_EVIDENCE_V2[after]
    if evidence_kind!=required_kind or evidence_path.parent.resolve()!=directory.resolve() or evidence_path.name!=required_name:
        raise MultiPanelCustodyError('state-specific durable evidence path required')
    if not evidence_path.is_file():raise MultiPanelCustodyError('state transition evidence missing')
    try:evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise MultiPanelCustodyError('state transition evidence invalid') from exc
    if type(evidence) is not dict or evidence.get('schema')!=required_schema or evidence.get('self_hash')!=_hash({k:v for k,v in evidence.items() if k!='self_hash'}):
        raise MultiPanelCustodyError('state transition evidence self-hash/schema mismatch')
    if set(evidence)!=_TRANSITION_EVIDENCE_KEYS_V2[after]:raise MultiPanelCustodyError('state transition evidence fields mismatch')
    if evidence_path.read_bytes()!=canonical_json_line_v2(evidence) or evidence.get('self_hash')!=evidence_hash:
        raise MultiPanelCustodyError('state transition evidence replay mismatch')
    for key in ('census_authority_hash','evaluation_policy_hash','metric_authority_hash','p1_custodian_authority_hash','dg05_authorization_hash'):
        if key in evidence:
            _sha(evidence[key],key)
            if evidence[key]!=current.get(key):raise MultiPanelCustodyError('transition evidence authority mismatch')
    if evidence.get('source_commit')!=current.get('source_commit'):raise MultiPanelCustodyError('transition evidence source mismatch')
    if after is GlobalPredictionStateV1.ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED:
        physical_document=_read_canonical_self_hashed_v2(directory/'physical-file-authority-v2.json','multipanel_physical_attack_file_authority_v2')
        census_document=_read_canonical_self_hashed_v2(directory/'global-cell-census-authority-v2.json','multipanel_global_cell_census_authority_v2')
        physical=_physical_from_document_v2(physical_document);census=_census_from_document_v2(census_document)
        if census.document()['self_hash']!=current.get('census_authority_hash') or census.physical_file_authority_hash!=physical.document()['self_hash']:
            raise MultiPanelCustodyError('projection census root authority mismatch')
        records=evidence.get('projection_records');count=evidence.get('projection_artifact_count')
        expected=tuple((panel,file_id) for panel,files in census.files_by_panel for file_id in files)
        if type(count) is not int or count!=len(expected) or type(records) is not list or len(records)!=count:
            raise MultiPanelCustodyError('projection census evidence incomplete')
        actual=[]
        for record in records:
            if type(record) is not dict or set(record)!={'panel_id','file_id','receipt','artifact_relative_path','artifact_file_hash'}:
                raise MultiPanelCustodyError('projection census record fields mismatch')
            cell=(record['panel_id'],record['file_id']);actual.append(cell)
            receipt=_projection_from_document_v2(record['receipt']);receipt.validate(frozen_feature_allowlist_authorities_v2()[cell[0]],physical)
            if (receipt.panel_id,receipt.file_id)!=cell:raise MultiPanelCustodyError('projection census cell mismatch')
            relative=Path(record['artifact_relative_path'])
            if relative.is_absolute() or '..' in relative.parts:raise MultiPanelCustodyError('unsafe projection artifact locator')
            artifact_path=(directory/relative).resolve()
            try:artifact_path.relative_to(directory.resolve())
            except ValueError as exc:raise MultiPanelCustodyError('projection artifact outside custody directory') from exc
            _sha(record['artifact_file_hash'],'artifact_file_hash')
            if (not artifact_path.is_file() or sha256(artifact_path.read_bytes()).hexdigest()!=record['artifact_file_hash']
                    or not replay_projection_artifact_v2(artifact_path,receipt)):
                raise MultiPanelCustodyError('projection census artifact replay mismatch')
        if tuple(actual)!=expected:raise MultiPanelCustodyError('projection census cells differ from frozen census')
    if after is GlobalPredictionStateV1.PREDICTIONS_IN_PROGRESS_LABEL_LOCKED and evidence.get('projection_transition_hash')!=current.get('self_hash'):
        raise MultiPanelCustodyError('prediction start does not bind projection transition')
    if after is GlobalPredictionStateV1.PREDICTIONS_IN_PROGRESS_LABEL_LOCKED and evidence.get('projection_census_hash')!=current.get('evidence_hash'):
        raise MultiPanelCustodyError('prediction start does not bind projection census evidence')
    if after is GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED:
        transition_zero=_read_canonical_self_hashed_v2(directory/'custody-transition-000.json','multipanel_global_custody_transition_v2')
        transition_one=_read_canonical_self_hashed_v2(directory/'custody-transition-001.json','multipanel_global_custody_transition_v2')
        if (transition_one.get('predecessor_receipt_hash')!=transition_zero['self_hash']
                or transition_one.get('evidence_kind')!='FEATURE_PROJECTION_CENSUS_FREEZE'):
            raise MultiPanelCustodyError('global transition projection predecessor mismatch')
        _validate_transition_evidence_v2(directory,transition_zero,
            GlobalPredictionStateV1.ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED,
            transition_one['evidence_kind'],transition_one['evidence_hash'],directory/'feature-projection-census.freeze.json')
        manifest_path=directory/'global_prediction_manifest_v2.json'
        if not manifest_path.is_file() or sha256(manifest_path.read_bytes()).hexdigest()!=evidence.get('manifest_file_hash'):
            raise MultiPanelCustodyError('global transition manifest bytes missing')
        try:manifest_document=json.loads(manifest_path.read_text(encoding='utf-8'))
        except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise MultiPanelCustodyError('global transition manifest invalid') from exc
        census=_census_from_document_v2(_read_canonical_self_hashed_v2(directory/'global-cell-census-authority-v2.json','multipanel_global_cell_census_authority_v2'))
        physical=_physical_from_document_v2(_read_canonical_self_hashed_v2(directory/'physical-file-authority-v2.json','multipanel_physical_attack_file_authority_v2'))
        manifest=_manifest_from_document_v2(manifest_document,census);manifest.validate(frozen_feature_allowlist_authorities_v2(),physical)
        if (manifest_path.read_bytes()!=canonical_json_line_v2(manifest_document)
                or manifest_document.get('self_hash')!=_hash({k:v for k,v in manifest_document.items() if k!='self_hash'})
                or manifest_document.get('self_hash')!=evidence.get('manifest_self_hash')
                or manifest_document.get('schema')!='multipanel_global_prediction_manifest_v2'
                or manifest_document.get('census_authority_hash')!=current.get('census_authority_hash')
                or manifest_document.get('evaluation_policy_hash')!=current.get('evaluation_policy_hash')
                or manifest_document.get('metric_authority_hash')!=current.get('metric_authority_hash')
                or manifest_document.get('p1_custodian_authority_hash')!=current.get('p1_custodian_authority_hash')
                or manifest_document.get('dg05_authorization_hash')!=current.get('dg05_authorization_hash')
                or manifest_document.get('state')!=GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED.value):
            raise MultiPanelCustodyError('global transition manifest authority mismatch')
        success_count=sum(type(item) is PredictionSuccessReceiptV2 for item in manifest.receipts)
        if (evidence.get('census_authority_hash')!=census.document()['self_hash']
                or evidence.get('physical_file_authority_hash')!=physical.document()['self_hash']
                or evidence.get('projection_artifact_count')!=len(manifest.projection_receipts)
                or evidence.get('prediction_artifact_count')!=success_count
                or evidence.get('state')!=GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED.value):
            raise MultiPanelCustodyError('global transition freeze census mismatch')
        if evidence.get('projection_receipt_hashes')!=[item.document()['self_hash'] for item in manifest.projection_receipts]:
            raise MultiPanelCustodyError('global transition projection receipt census mismatch')
        if evidence.get('terminal_receipt_hashes')!=[item.document()['self_hash'] for item in manifest.receipts]:
            raise MultiPanelCustodyError('global transition terminal receipt census mismatch')
        success={(item.panel_id,item.file_id,item.method_id):item for item in manifest.receipts if type(item) is PredictionSuccessReceiptV2}
        records=evidence.get('prediction_records')
        if type(records) is not list or len(records)!=len(success):raise MultiPanelCustodyError('global prediction artifact census mismatch')
        actual=[]
        for record in records:
            if type(record) is not dict or set(record)!={'panel_id','file_id','method_id','artifact_relative_path','artifact_file_hash'}:
                raise MultiPanelCustodyError('global prediction artifact record fields mismatch')
            cell=(record['panel_id'],record['file_id'],record['method_id']);actual.append(cell)
            if cell not in success:raise MultiPanelCustodyError('global prediction artifact cell mismatch')
            relative=Path(record['artifact_relative_path'])
            if relative.is_absolute() or '..' in relative.parts:raise MultiPanelCustodyError('unsafe prediction artifact locator')
            artifact_path=(directory/relative).resolve()
            try:artifact_path.relative_to(directory.resolve())
            except ValueError as exc:raise MultiPanelCustodyError('prediction artifact outside custody directory') from exc
            _sha(record['artifact_file_hash'],'prediction_artifact_file_hash')
            if (not artifact_path.is_file() or sha256(artifact_path.read_bytes()).hexdigest()!=record['artifact_file_hash']
                    or not replay_prediction_artifact_v2(artifact_path,success[cell])):
                raise MultiPanelCustodyError('global prediction artifact replay mismatch')
        if tuple(actual)!=tuple(success):raise MultiPanelCustodyError('global prediction artifact order mismatch')
    if after is GlobalPredictionStateV1.LABEL_SCENARIO_LEASE_OPEN and evidence.get('transition_receipt_hash')!=current.get('self_hash'):
        raise MultiPanelCustodyError('lease issue does not bind global freeze transition')
    if after is GlobalPredictionStateV1.RESULTS_COMPUTED and evidence.get('lease_open_transition_hash')!=current.get('self_hash'):
        raise MultiPanelCustodyError('result receipt does not bind lease-open transition')
    return evidence


def advance_state_chain_v2(directory:Path,current:Mapping[str,Any],after:GlobalPredictionStateV1,*,evidence_kind:str,
                           evidence_hash:str,evidence_path:Path)->dict[str,Any]:
    validate_transition_receipt_v2(directory,current)
    before=GlobalPredictionStateV1(current['state']);validate_state_transition_v1(before,after)
    _sha(evidence_hash,'transition_evidence_hash')
    _validate_transition_evidence_v2(directory,current,after,evidence_kind,evidence_hash,evidence_path)
    body={key:value for key,value in current.items() if key not in ('self_hash','sequence','state','predecessor_receipt_hash')}
    body.update({'sequence':current['sequence']+1,'state':after.value,'predecessor_receipt_hash':current['self_hash'],
                 'evidence_kind':evidence_kind,'evidence_hash':evidence_hash})
    body={**body,'self_hash':_hash(body)};_publish_new(directory/f"custody-transition-{body['sequence']:03d}.json",canonical_json_line_v2(body));return body


def validate_transition_receipt_v2(directory:Path,receipt:Mapping[str,Any])->None:
    if type(receipt) is not dict or receipt.get('self_hash')!=_hash({k:v for k,v in receipt.items() if k!='self_hash'}):raise MultiPanelCustodyError('invalid transition self hash')
    sequence=receipt.get('sequence');path=directory/f'custody-transition-{sequence:03d}.json'
    if type(sequence) is not int or not path.is_file() or path.read_bytes()!=canonical_json_line_v2(receipt):raise MultiPanelCustodyError('durable transition replay failed')
    if sequence:
        prior_path=directory/f'custody-transition-{sequence-1:03d}.json'
        if not prior_path.is_file():raise MultiPanelCustodyError('missing transition predecessor')
        prior=json.loads(prior_path.read_text(encoding='utf-8'))
        if prior.get('self_hash')!=_hash({k:v for k,v in prior.items() if k!='self_hash'}) or receipt.get('predecessor_receipt_hash')!=prior.get('self_hash'):
            raise MultiPanelCustodyError('transition chain broken')


_LEASE_SENTINEL=object()
class LabelScenarioLeaseV2:
    __slots__=('__token','manifest_hash','issue_receipt_hash','lease_open_transition_hash','directory')
    def __init__(self,sentinel:object,token:str,manifest_hash:str,issue_receipt_hash:str,lease_open_transition_hash:str,directory:Path):
        if sentinel is not _LEASE_SENTINEL:raise MultiPanelCustodyError('lease constructor is private')
        self.__token=token;self.manifest_hash=manifest_hash;self.issue_receipt_hash=issue_receipt_hash
        self.lease_open_transition_hash=lease_open_transition_hash;self.directory=directory
    def token_hash(self)->str:return sha256(self.__token.encode()).hexdigest()
    def __repr__(self)->str:return 'LabelScenarioLeaseV2(<opaque>)'


def issue_label_scenario_lease_v2(directory:Path,manifest:GlobalPredictionManifestV2,
                                  freeze_receipt:Mapping[str,Any],transition_receipt:Mapping[str,Any],
                                  allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2],physical:FrozenPhysicalFileAuthorityV2,
                                  projection_artifacts:Mapping[tuple[str,str],Path],
                                  prediction_artifacts:Mapping[tuple[str,str,str],Path])->LabelScenarioLeaseV2:
    manifest.validate(allowlists,physical);validate_transition_receipt_v2(directory,transition_receipt)
    if transition_receipt['state']!=GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED.value:raise MultiPanelCustodyError('global frozen transition required')
    manifest_path=directory/'global_prediction_manifest_v2.json';freeze_path=directory/'global_prediction_manifest_v2.freeze.json'
    if not manifest_path.is_file() or not freeze_path.is_file() or json.loads(freeze_path.read_text(encoding='utf-8'))!=dict(freeze_receipt):raise MultiPanelCustodyError('durable manifest freeze required')
    if freeze_receipt.get('self_hash')!=_hash({k:v for k,v in freeze_receipt.items() if k!='self_hash'}):raise MultiPanelCustodyError('invalid freeze receipt self hash')
    document=manifest.document()
    if sha256(manifest_path.read_bytes()).hexdigest()!=freeze_receipt.get('manifest_file_hash') or document['self_hash']!=freeze_receipt.get('manifest_self_hash'):
        raise MultiPanelCustodyError('manifest freeze mismatch')
    _replay_frozen_artifacts_v2(manifest,projection_artifacts,prediction_artifacts)
    if transition_receipt.get('evidence_kind')!='GLOBAL_MANIFEST_FREEZE' or transition_receipt.get('evidence_hash')!=freeze_receipt['self_hash']:
        raise MultiPanelCustodyError('global freeze transition evidence mismatch')
    for key in ('census_authority_hash','evaluation_policy_hash','metric_authority_hash','p1_custodian_authority_hash','dg05_authorization_hash'):
        expected=manifest.census.document()['self_hash'] if key=='census_authority_hash' else getattr(manifest,key)
        if transition_receipt.get(key)!=expected:raise MultiPanelCustodyError('transition/manifest authority mismatch')
    token=secrets.token_hex(32);token_hash=sha256(token.encode()).hexdigest()
    body={'schema':'multipanel_label_scenario_lease_issue_v2','manifest_hash':document['self_hash'],
          'manifest_file_hash':freeze_receipt['manifest_file_hash'],'transition_receipt_hash':transition_receipt['self_hash'],
          'census_authority_hash':manifest.census.document()['self_hash'],'evaluation_policy_hash':manifest.evaluation_policy_hash,
          'metric_authority_hash':manifest.metric_authority_hash,'p1_custodian_authority_hash':manifest.p1_custodian_authority_hash,
          'dg05_authorization_hash':manifest.dg05_authorization_hash,'token_hash':token_hash,'source_commit':manifest.source_commit}
    body={**body,'self_hash':_hash(body)};issue_path=directory/'label-scenario-lease.issue.json'
    _publish_new(issue_path,canonical_json_line_v2(body))
    lease_transition=advance_state_chain_v2(directory,transition_receipt,GlobalPredictionStateV1.LABEL_SCENARIO_LEASE_OPEN,
        evidence_kind='LABEL_SCENARIO_LEASE_ISSUE',evidence_hash=body['self_hash'],evidence_path=issue_path)
    return LabelScenarioLeaseV2(_LEASE_SENTINEL,token,document['self_hash'],body['self_hash'],lease_transition['self_hash'],directory)


def consume_label_scenario_lease_v2(lease:LabelScenarioLeaseV2,manifest:GlobalPredictionManifestV2,
                                    allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2],physical:FrozenPhysicalFileAuthorityV2,
                                    projection_artifacts:Mapping[tuple[str,str],Path],prediction_artifacts:Mapping[tuple[str,str,str],Path],
                                    reader:Callable[[],Any])->Any:
    if type(lease) is not LabelScenarioLeaseV2 or not callable(reader):raise MultiPanelCustodyError('valid opaque lease and reader required')
    manifest.validate(allowlists,physical);document=manifest.document();directory=lease.directory
    issue_path=directory/'label-scenario-lease.issue.json'
    if not issue_path.is_file():raise MultiPanelCustodyError('durable lease issue missing')
    issue=json.loads(issue_path.read_text(encoding='utf-8'))
    if issue.get('self_hash')!=_hash({k:v for k,v in issue.items() if k!='self_hash'}):raise MultiPanelCustodyError('lease issue self hash mismatch')
    if (issue.get('self_hash'),issue.get('manifest_hash'),issue.get('token_hash'))!=(lease.issue_receipt_hash,document['self_hash'],lease.token_hash()):
        raise MultiPanelCustodyError('lease authority mismatch')
    transition_path=directory/'custody-transition-004.json'
    if not transition_path.is_file():raise MultiPanelCustodyError('lease-open transition missing')
    lease_transition=json.loads(transition_path.read_text(encoding='utf-8'));validate_transition_receipt_v2(directory,lease_transition)
    if (lease_transition.get('self_hash'),lease_transition.get('state'),lease_transition.get('evidence_hash'))!=(lease.lease_open_transition_hash,GlobalPredictionStateV1.LABEL_SCENARIO_LEASE_OPEN.value,issue['self_hash']):
        raise MultiPanelCustodyError('lease-open transition mismatch')
    manifest_path=directory/'global_prediction_manifest_v2.json';before=sha256(manifest_path.read_bytes()).hexdigest()
    if before!=issue.get('manifest_file_hash'):raise MultiPanelCustodyError('manifest mutated after lease issue')
    _replay_frozen_artifacts_v2(manifest,projection_artifacts,prediction_artifacts)
    consumed={'schema':'multipanel_label_scenario_lease_consumed_v2','issue_receipt_hash':issue['self_hash'],
              'manifest_hash':document['self_hash'],'manifest_file_hash_before':before,'token_hash':lease.token_hash(),
              'source_commit':manifest.source_commit}
    consumed={**consumed,'self_hash':_hash(consumed)}
    _publish_new(directory/'label-scenario-lease.consumed.json',canonical_json_line_v2(consumed))
    try:
        result=reader();reader_status='SUCCESS';caught=False
    except BaseException:
        reader_status='READER_FAILED_LEASE_CONSUMED';result=None;caught=True
    after=sha256(manifest_path.read_bytes()).hexdigest()
    if after!=before:
        reader_status='POST_READ_MANIFEST_MUTATION';result=None;caught=True
    try:_replay_frozen_artifacts_v2(manifest,projection_artifacts,prediction_artifacts)
    except MultiPanelCustodyError:
        reader_status='POST_READ_FROZEN_ARTIFACT_MUTATION';result=None;caught=True
    completed={'schema':'multipanel_label_scenario_lease_completion_v2','consumed_receipt_hash':consumed['self_hash'],
               'manifest_file_hash_after':after,'reader_status':reader_status,'source_commit':manifest.source_commit}
    completed={**completed,'self_hash':_hash(completed)}
    _publish_new(directory/'label-scenario-lease.completed.json',canonical_json_line_v2(completed))
    if caught:
        message='LABEL_READER_FAILED_LEASE_CONSUMED' if reader_status=='READER_FAILED_LEASE_CONSUMED' else reader_status
        raise MultiPanelCustodyError(message)
    return result


@dataclass(frozen=True,order=True)
class ResultRecordReceiptV2:
    panel_id:str; method_id:str; result_hash:str
    def document(self)->dict[str,str]:return dict(self.__dict__)
    def validate(self)->None:
        if self.panel_id not in FROZEN_PANEL_ORDER_V2:raise MultiPanelCustodyError('unknown result panel')
        if self.method_id not in PRIMARY_METHODS_V2+SECONDARY_METHODS_V2[self.panel_id]:raise MultiPanelCustodyError('unknown result method')
        _sha(self.result_hash,'result_hash')


def persist_result_bundle_v2(directory:Path,lease:LabelScenarioLeaseV2,
                             records:Sequence[ResultRecordReceiptV2])->dict[str,Any]:
    """Persist one hash-only result census after the one-shot lease is consumed."""
    if type(lease) is not LabelScenarioLeaseV2:raise MultiPanelCustodyError('typed label/scenario lease required')
    completion=_read_canonical_self_hashed_v2(directory/'label-scenario-lease.completed.json','multipanel_label_scenario_lease_completion_v2')
    issue=_read_canonical_self_hashed_v2(directory/'label-scenario-lease.issue.json','multipanel_label_scenario_lease_issue_v2')
    manifest=_read_canonical_self_hashed_v2(directory/'global_prediction_manifest_v2.json','multipanel_global_prediction_manifest_v2')
    if (completion.get('reader_status')!='SUCCESS' or issue['self_hash']!=lease.issue_receipt_hash
            or manifest['self_hash']!=lease.manifest_hash):raise MultiPanelCustodyError('result bundle lease authority mismatch')
    expected=tuple((panel,method_id) for panel in FROZEN_PANEL_ORDER_V2
                   for method_id in PRIMARY_METHODS_V2+SECONDARY_METHODS_V2[panel])
    actual=[]
    for record in records:
        if type(record) is not ResultRecordReceiptV2:raise MultiPanelCustodyError('typed result record required')
        record.validate();actual.append((record.panel_id,record.method_id))
    if tuple(actual)!=expected:raise MultiPanelCustodyError('exact result record census required')
    body={'schema':'multipanel_result_bundle_v2','manifest_hash':manifest['self_hash'],
          'lease_issue_receipt_hash':issue['self_hash'],'lease_completion_receipt_hash':completion['self_hash'],
          'metric_authority_hash':FROZEN_METRIC_AUTHORITY_HASH_V2,
          'p1_custodian_authority_hash':FROZEN_P1_CUSTODIAN_AUTHORITY_HASH_V2,
          'records':[record.document() for record in records],'source_commit':FROZEN_AUTHORITY_SOURCE_COMMIT_V2}
    body={**body,'self_hash':_hash(body)}
    _publish_new(directory/'result-bundle.json',canonical_json_line_v2(body));return body


def complete_results_state_v2(directory:Path,lease:LabelScenarioLeaseV2,result_integrity_receipt:Mapping[str,Any])->dict[str,Any]:
    """Close only after replaying the exact durable result census and its authority chain."""
    if type(lease) is not LabelScenarioLeaseV2:raise MultiPanelCustodyError('typed label/scenario lease required')
    transition_path=directory/'custody-transition-004.json'
    completion_path=directory/'label-scenario-lease.completed.json'
    if not transition_path.is_file() or not completion_path.is_file():raise MultiPanelCustodyError('completed label lease required')
    current=json.loads(transition_path.read_text(encoding='utf-8'));validate_transition_receipt_v2(directory,current)
    if (current.get('state')!=GlobalPredictionStateV1.LABEL_SCENARIO_LEASE_OPEN.value
            or current.get('self_hash')!=lease.lease_open_transition_hash):raise MultiPanelCustodyError('lease-open state authority mismatch')
    completion=_read_canonical_self_hashed_v2(completion_path,'multipanel_label_scenario_lease_completion_v2')
    if completion.get('reader_status')!='SUCCESS':raise MultiPanelCustodyError('successful label lease completion required')
    consumed=_read_canonical_self_hashed_v2(directory/'label-scenario-lease.consumed.json','multipanel_label_scenario_lease_consumed_v2')
    issue=_read_canonical_self_hashed_v2(directory/'label-scenario-lease.issue.json','multipanel_label_scenario_lease_issue_v2')
    if (completion.get('consumed_receipt_hash')!=consumed['self_hash'] or consumed.get('issue_receipt_hash')!=issue['self_hash']
            or issue['self_hash']!=lease.issue_receipt_hash or issue.get('manifest_hash')!=lease.manifest_hash):
        raise MultiPanelCustodyError('result lease receipt chain mismatch')
    manifest=_read_canonical_self_hashed_v2(directory/'global_prediction_manifest_v2.json','multipanel_global_prediction_manifest_v2')
    if manifest['self_hash']!=lease.manifest_hash:raise MultiPanelCustodyError('result manifest authority mismatch')
    result_path=directory/'result-bundle.json'
    result_bundle=_read_canonical_self_hashed_v2(result_path,'multipanel_result_bundle_v2')
    result_exact={'schema','manifest_hash','lease_issue_receipt_hash','lease_completion_receipt_hash','metric_authority_hash',
                  'p1_custodian_authority_hash','records','source_commit','self_hash'}
    if set(result_bundle)!=result_exact or type(result_bundle.get('records')) is not list:
        raise MultiPanelCustodyError('result bundle fields mismatch')
    expected=tuple((panel,method_id) for panel in FROZEN_PANEL_ORDER_V2
                   for method_id in PRIMARY_METHODS_V2+SECONDARY_METHODS_V2[panel])
    actual=[]
    for item in result_bundle['records']:
        if type(item) is not dict or set(item)!={'panel_id','method_id','result_hash'}:raise MultiPanelCustodyError('result record fields mismatch')
        record=ResultRecordReceiptV2(**item);record.validate();actual.append((record.panel_id,record.method_id))
    if tuple(actual)!=expected:raise MultiPanelCustodyError('result record census mismatch')
    if (result_bundle['manifest_hash']!=manifest['self_hash']
            or result_bundle['lease_issue_receipt_hash']!=issue['self_hash']
            or result_bundle['lease_completion_receipt_hash']!=completion['self_hash']
            or result_bundle['metric_authority_hash']!=current['metric_authority_hash']
            or result_bundle['p1_custodian_authority_hash']!=current['p1_custodian_authority_hash']
            or result_bundle['source_commit']!=current['source_commit']):
        raise MultiPanelCustodyError('result bundle authority mismatch')
    body=dict(result_integrity_receipt)
    allowed_without_hash=_TRANSITION_EVIDENCE_KEYS_V2[GlobalPredictionStateV1.RESULTS_COMPUTED]-{'self_hash'}
    if set(body) not in (allowed_without_hash,_TRANSITION_EVIDENCE_KEYS_V2[GlobalPredictionStateV1.RESULTS_COMPUTED]):
        raise MultiPanelCustodyError('result integrity fields mismatch')
    expected_values={'schema':'multipanel_result_integrity_receipt_v2','lease_completion_receipt_hash':completion['self_hash'],
        'lease_open_transition_hash':lease.lease_open_transition_hash,'manifest_hash':manifest['self_hash'],
        'result_bundle_self_hash':result_bundle['self_hash'],'result_bundle_file_hash':sha256(result_path.read_bytes()).hexdigest(),
        'result_record_count':len(expected),'source_commit':current['source_commit']}
    if any(body.get(key)!=value for key,value in expected_values.items()):
        raise MultiPanelCustodyError('result integrity authority mismatch')
    if 'self_hash' in body:
        if body['self_hash']!=_hash({k:v for k,v in body.items() if k!='self_hash'}):raise MultiPanelCustodyError('result integrity self hash mismatch')
    else:body={**body,'self_hash':_hash(body)}
    path=directory/'result-integrity.receipt.json';_publish_new(path,canonical_json_line_v2(body))
    return advance_state_chain_v2(directory,current,GlobalPredictionStateV1.RESULTS_COMPUTED,
        evidence_kind='RESULT_INTEGRITY_RECEIPT',evidence_hash=body['self_hash'],evidence_path=path)


def build_prediction_artifact_v2(receipt:PredictionSuccessReceiptV2,alarms:Sequence[bool])->bytes:
    if any(type(value) is not bool for value in alarms) or len(alarms)!=receipt.row_count or sum(alarms)!=receipt.alarm_count:
        raise MultiPanelCustodyError('prediction stream census mismatch')
    body={'schema':'multipanel_prediction_artifact_v2','panel_id':receipt.panel_id,'file_id':receipt.file_id,
          'method_id':receipt.method_id,'method_authority_hash':receipt.method_authority_hash,
          'execution_authority_hash':receipt.execution_authority_hash,'feature_projection_hash':receipt.feature_projection_hash,
          'row_count':receipt.row_count,'timestamp_range_hash':receipt.timestamp_range_hash,'alarms':list(alarms)}
    body={**body,'self_hash':_hash(body)};return canonical_json_line_v2(body)


def replay_prediction_artifact_v2(path:Path,receipt:PredictionSuccessReceiptV2)->bool:
    payload=path.read_bytes()
    if sha256(payload).hexdigest()!=receipt.prediction_artifact_hash:return False
    try:value=json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError,json.JSONDecodeError):return False
    if value.get('self_hash')!=_hash({k:v for k,v in value.items() if k!='self_hash'}):return False
    exact={'schema':'multipanel_prediction_artifact_v2','panel_id':receipt.panel_id,'file_id':receipt.file_id,
           'method_id':receipt.method_id,'method_authority_hash':receipt.method_authority_hash,
           'execution_authority_hash':receipt.execution_authority_hash,'feature_projection_hash':receipt.feature_projection_hash,
           'row_count':receipt.row_count,'timestamp_range_hash':receipt.timestamp_range_hash}
    if any(value.get(key)!=expected for key,expected in exact.items()):return False
    alarms=value.get('alarms')
    return isinstance(alarms,list) and len(alarms)==receipt.row_count and all(type(v) is bool for v in alarms) and sum(alarms)==receipt.alarm_count


def _replay_frozen_artifacts_v2(manifest:GlobalPredictionManifestV2,projection_artifacts:Mapping[tuple[str,str],Path],
                                prediction_artifacts:Mapping[tuple[str,str,str],Path])->None:
    projections={(r.panel_id,r.file_id):r for r in manifest.projection_receipts}
    success={(r.panel_id,r.file_id,r.method_id):r for r in manifest.receipts if type(r) is PredictionSuccessReceiptV2}
    if set(projection_artifacts)!=set(projections) or set(prediction_artifacts)!=set(success):raise MultiPanelCustodyError('frozen artifact census mismatch')
    for cell,path in projection_artifacts.items():
        if not path.is_file() or not replay_projection_artifact_v2(path,projections[cell]):raise MultiPanelCustodyError('projection artifact mutated')
    for cell,path in prediction_artifacts.items():
        if not path.is_file() or not replay_prediction_artifact_v2(path,success[cell]):raise MultiPanelCustodyError('prediction artifact mutated')


__all__=['GlobalPredictionStateV1','PredictionCellReceiptV1','GlobalPredictionManifestV1','LabelScenarioLeaseV1',
         'issue_label_scenario_lease_v1','consume_label_scenario_lease_v1','validate_attack_feature_projection_contract_v1',
         'project_attack_columns_v1','validate_state_transition_v1','MultiPanelCustodyError',
         'FROZEN_PANEL_ORDER_V2','PRIMARY_METHODS_V2','SECONDARY_METHODS_V2','FrozenFeatureAllowlistAuthorityV2',
         'AttackFeatureProjectionReceiptV2','MethodCellAuthorityV2','GlobalCellCensusAuthorityV2',
         'PredictionSuccessReceiptV2','PredictionFailureReceiptV2','GlobalPredictionManifestV2',
         'project_attack_columns_v2','canonical_projection_bytes_v2','persist_global_manifest_v2',
         'PhysicalFileIdentityV2','FrozenPhysicalFileAuthorityV2','replay_projection_artifact_v2',
         'initialize_state_chain_v2','advance_state_chain_v2','validate_transition_receipt_v2',
         'LabelScenarioLeaseV2','issue_label_scenario_lease_v2','consume_label_scenario_lease_v2',
         'ResultRecordReceiptV2','persist_result_bundle_v2','complete_results_state_v2',
         'build_prediction_artifact_v2','replay_prediction_artifact_v2','persist_projection_census_v2',
         'FROZEN_DATASET_VERSIONS_V2','FROZEN_TIMESTAMP_IDS_V2','FROZEN_FEATURE_IDS_V2',
         'FROZEN_ATTACK_FILE_IDS_V2','FROZEN_ATTACK_FILE_CENSUS_HASH_V2',
         'FROZEN_METHOD_BUNDLE_HASH_V2','FROZEN_AUTHORITY_SOURCE_COMMIT_V2','FROZEN_METRIC_AUTHORITY_HASH_V2',
         'FROZEN_P1_CUSTODIAN_AUTHORITY_HASH_V2','frozen_feature_allowlist_authorities_v2',
         'frozen_method_cell_authorities_v2']
