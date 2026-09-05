"""Global all-panel prediction-before-any-label custody contracts.

The module is prospective and synthetic-testable.  It cannot read datasets;
callers must present hash-only receipts from the existing durable custody layer.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import secrets
from typing import Any, Callable, Mapping, Sequence


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
    try:
        with path.open('xb') as handle:
            handle.write(payload);handle.flush()
    except FileExistsError as exc:
        raise MultiPanelCustodyError('APPEND_ONLY_ARTIFACT_CONFLICT') from exc
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
        _identity(self.dataset_version,'dataset_version');_identity(self.timestamp_id,'timestamp_id')
        if not self.feature_ids or len(set(self.feature_ids))!=len(self.feature_ids):raise MultiPanelCustodyError('exact feature allowlist required')
        if any(type(v) is not str or not v.startswith('P1_') for v in self.feature_ids):raise MultiPanelCustodyError('positive P1 feature allowlist required')
        _sha(self.method_bundle_hash,'method_bundle_hash');_gitsha(self.source_commit,'source_commit')


@dataclass(frozen=True)
class AttackFeatureProjectionReceiptV2:
    panel_id:str; file_id:str; timestamp_id:str; approved_feature_ids:tuple[str,...]
    feature_allowlist_authority_hash:str; raw_container_hash:str; header_hash:str
    projection_hash:str; row_count:int; timestamp_range_hash:str; source_commit:str
    label_values_parsed:bool=False; label_values_decoded:bool=False; label_values_inspected:bool=False
    label_values_counted:bool=False; label_values_validated:bool=False; label_values_filtered_on:bool=False
    label_values_used:bool=False; scenario_values_parsed:bool=False; scenario_values_used:bool=False
    def document(self)->dict[str,Any]:
        body={'schema':'multipanel_attack_feature_projection_receipt_v2',**self.__dict__}
        body['approved_feature_ids']=list(self.approved_feature_ids)
        return {**body,'self_hash':_hash(body)}
    def validate(self,authority:FrozenFeatureAllowlistAuthorityV2)->None:
        if type(authority) is not FrozenFeatureAllowlistAuthorityV2:raise MultiPanelCustodyError('typed allowlist authority required')
        authority.validate()
        if (self.panel_id,self.timestamp_id,self.approved_feature_ids)!=(authority.panel_id,authority.timestamp_id,authority.feature_ids):
            raise MultiPanelCustodyError('projection is not bound to exact allowlist')
        if self.feature_allowlist_authority_hash!=authority.document()['self_hash']:raise MultiPanelCustodyError('allowlist authority hash mismatch')
        _identity(self.file_id,'file_id');_gitsha(self.source_commit,'source_commit')
        for name in ('feature_allowlist_authority_hash','raw_container_hash','header_hash','projection_hash','timestamp_range_hash'):_sha(getattr(self,name),name)
        if type(self.row_count) is not int or self.row_count<=0:raise MultiPanelCustodyError('invalid projection row count')
        flags=(self.label_values_parsed,self.label_values_decoded,self.label_values_inspected,self.label_values_counted,
               self.label_values_validated,self.label_values_filtered_on,self.label_values_used,self.scenario_values_parsed,self.scenario_values_used)
        if any(type(v) is not bool or v for v in flags):raise MultiPanelCustodyError('excluded label/scenario value contact')


@dataclass(frozen=True)
class MethodCellAuthorityV2:
    method_id:str; method_authority_hash:str; execution_authority_hash:str
    def validate(self)->None:
        _identity(self.method_id,'method_id');_sha(self.method_authority_hash,'method_authority_hash');_sha(self.execution_authority_hash,'execution_authority_hash')
    def document(self)->dict[str,str]:return dict(self.__dict__)


@dataclass(frozen=True)
class GlobalCellCensusAuthorityV2:
    files_by_panel:tuple[tuple[str,tuple[str,...]],...]
    methods_by_panel:tuple[tuple[str,tuple[MethodCellAuthorityV2,...]],...]
    method_bundle_hash:str; physical_file_authority_hash:str; source_commit:str
    def validate(self)->None:
        if tuple(panel for panel,_ in self.files_by_panel)!=FROZEN_PANEL_ORDER_V2 or tuple(panel for panel,_ in self.methods_by_panel)!=FROZEN_PANEL_ORDER_V2:
            raise MultiPanelCustodyError('exact frozen panel order required')
        for panel,files in self.files_by_panel:
            if not files or len(set(files))!=len(files):raise MultiPanelCustodyError('exact physical file census required')
            for value in files:_identity(value,'file_id')
        for panel,methods in self.methods_by_panel:
            expected=PRIMARY_METHODS_V2+SECONDARY_METHODS_V2[panel]
            if tuple(item.method_id for item in methods)!=expected:raise MultiPanelCustodyError('exact frozen method census required')
            for item in methods:item.validate()
        _sha(self.method_bundle_hash,'method_bundle_hash');_sha(self.physical_file_authority_hash,'physical_file_authority_hash');_gitsha(self.source_commit,'source_commit')
    def body(self)->dict[str,Any]:
        return {'schema':'multipanel_global_cell_census_authority_v2','files_by_panel':[[p,list(v)] for p,v in self.files_by_panel],
                'methods_by_panel':[[p,[m.document() for m in v]] for p,v in self.methods_by_panel],
                'method_bundle_hash':self.method_bundle_hash,'physical_file_authority_hash':self.physical_file_authority_hash,
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
    census.validate();_identity(receipt.file_id,'file_id');_gitsha(receipt.source_commit,'source_commit')
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
    def validate(self,allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2])->None:
        self.census.validate();_gitsha(self.source_commit,'source_commit')
        for name in ('evaluation_policy_hash','metric_authority_hash','p1_custodian_authority_hash','dg05_authorization_hash'):_sha(getattr(self,name),name)
        if self.state is not GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED:raise MultiPanelCustodyError('global label-locked freeze required')
        files={(panel,file_id) for panel,values in self.census.files_by_panel for file_id in values}
        projections={(item.panel_id,item.file_id):item for item in self.projection_receipts}
        if len(projections)!=len(self.projection_receipts) or set(projections)!=files:raise MultiPanelCustodyError('projection receipt census mismatch')
        for (panel,_),item in projections.items():
            if panel not in allowlists:raise MultiPanelCustodyError('missing allowlist authority')
            item.validate(allowlists[panel])
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
    authority.validate();_sha(raw_container_hash,'raw_container_hash');_gitsha(source_commit,'source_commit');_identity(file_id,'file_id')
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


def persist_global_manifest_v2(directory:Path,manifest:GlobalPredictionManifestV2,
                               allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2],
                               prediction_artifacts:Mapping[tuple[str,str,str],Path])->dict[str,Any]:
    manifest.validate(allowlists)
    success={(r.panel_id,r.file_id,r.method_id):r for r in manifest.receipts if type(r) is PredictionSuccessReceiptV2}
    if set(prediction_artifacts)!=set(success):raise MultiPanelCustodyError('success artifact census mismatch')
    for cell,path in prediction_artifacts.items():
        if not path.is_file() or sha256(path.read_bytes()).hexdigest()!=success[cell].prediction_artifact_hash:
            raise MultiPanelCustodyError('prediction artifact replay mismatch')
    body=manifest.document();payload=canonical_json_line_v2(body)
    manifest_path=directory/'global_prediction_manifest_v2.json';file_hash=_publish_new(manifest_path,payload)
    freeze={'schema':'multipanel_global_prediction_manifest_freeze_receipt_v2','manifest_self_hash':body['self_hash'],
            'manifest_file_hash':file_hash,'census_authority_hash':manifest.census.document()['self_hash'],
            'state':manifest.state.value,'source_commit':manifest.source_commit}
    freeze={**freeze,'self_hash':_hash(freeze)};_publish_new(directory/'global_prediction_manifest_v2.freeze.json',canonical_json_line_v2(freeze))
    return freeze


def canonical_json_line_v2(value:Mapping[str,Any])->bytes:return _canon(value)+b'\n'


def initialize_state_chain_v2(directory:Path,*,census_authority_hash:str,evaluation_policy_hash:str,
                              metric_authority_hash:str,p1_custodian_authority_hash:str,dg05_authorization_hash:str,
                              source_commit:str)->dict[str,Any]:
    for name,value in locals().copy().items():
        if name not in ('directory','source_commit'):_sha(value,name)
    _gitsha(source_commit,'source_commit')
    body={'schema':'multipanel_global_custody_transition_v2','sequence':0,'state':_STATE_ORDER[0].value,
          'predecessor_receipt_hash':None,'census_authority_hash':census_authority_hash,
          'evaluation_policy_hash':evaluation_policy_hash,'metric_authority_hash':metric_authority_hash,
          'p1_custodian_authority_hash':p1_custodian_authority_hash,'dg05_authorization_hash':dg05_authorization_hash,
          'source_commit':source_commit}
    body={**body,'self_hash':_hash(body)};_publish_new(directory/'custody-transition-000.json',canonical_json_line_v2(body));return body


def advance_state_chain_v2(directory:Path,current:Mapping[str,Any],after:GlobalPredictionStateV1)->dict[str,Any]:
    validate_transition_receipt_v2(directory,current)
    before=GlobalPredictionStateV1(current['state']);validate_state_transition_v1(before,after)
    body={key:value for key,value in current.items() if key not in ('self_hash','sequence','state','predecessor_receipt_hash')}
    body.update({'sequence':current['sequence']+1,'state':after.value,'predecessor_receipt_hash':current['self_hash']})
    body={**body,'self_hash':_hash(body)};_publish_new(directory/f"custody-transition-{body['sequence']:03d}.json",canonical_json_line_v2(body));return body


def validate_transition_receipt_v2(directory:Path,receipt:Mapping[str,Any])->None:
    if type(receipt) is not dict or receipt.get('self_hash')!=_hash({k:v for k,v in receipt.items() if k!='self_hash'}):raise MultiPanelCustodyError('invalid transition self hash')
    sequence=receipt.get('sequence');path=directory/f'custody-transition-{sequence:03d}.json'
    if type(sequence) is not int or not path.is_file() or path.read_bytes()!=canonical_json_line_v2(receipt):raise MultiPanelCustodyError('durable transition replay failed')
    if sequence:
        prior_path=directory/f'custody-transition-{sequence-1:03d}.json'
        if not prior_path.is_file():raise MultiPanelCustodyError('missing transition predecessor')
        prior=json.loads(prior_path.read_text(encoding='utf-8'))
        if receipt.get('predecessor_receipt_hash')!=prior.get('self_hash'):raise MultiPanelCustodyError('transition chain broken')


_LEASE_SENTINEL=object()
class LabelScenarioLeaseV2:
    __slots__=('__token','manifest_hash','issue_receipt_hash','directory')
    def __init__(self,sentinel:object,token:str,manifest_hash:str,issue_receipt_hash:str,directory:Path):
        if sentinel is not _LEASE_SENTINEL:raise MultiPanelCustodyError('lease constructor is private')
        self.__token=token;self.manifest_hash=manifest_hash;self.issue_receipt_hash=issue_receipt_hash;self.directory=directory
    def token_hash(self)->str:return sha256(self.__token.encode()).hexdigest()
    def __repr__(self)->str:return 'LabelScenarioLeaseV2(<opaque>)'


def issue_label_scenario_lease_v2(directory:Path,manifest:GlobalPredictionManifestV2,
                                  freeze_receipt:Mapping[str,Any],transition_receipt:Mapping[str,Any],
                                  allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2])->LabelScenarioLeaseV2:
    manifest.validate(allowlists);validate_transition_receipt_v2(directory,transition_receipt)
    if transition_receipt['state']!=GlobalPredictionStateV1.GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED.value:raise MultiPanelCustodyError('global frozen transition required')
    manifest_path=directory/'global_prediction_manifest_v2.json';freeze_path=directory/'global_prediction_manifest_v2.freeze.json'
    if not manifest_path.is_file() or not freeze_path.is_file() or json.loads(freeze_path.read_text(encoding='utf-8'))!=dict(freeze_receipt):raise MultiPanelCustodyError('durable manifest freeze required')
    document=manifest.document()
    if sha256(manifest_path.read_bytes()).hexdigest()!=freeze_receipt.get('manifest_file_hash') or document['self_hash']!=freeze_receipt.get('manifest_self_hash'):
        raise MultiPanelCustodyError('manifest freeze mismatch')
    for key in ('census_authority_hash','evaluation_policy_hash','metric_authority_hash','p1_custodian_authority_hash','dg05_authorization_hash'):
        expected=manifest.census.document()['self_hash'] if key=='census_authority_hash' else getattr(manifest,key)
        if transition_receipt.get(key)!=expected:raise MultiPanelCustodyError('transition/manifest authority mismatch')
    token=secrets.token_hex(32);token_hash=sha256(token.encode()).hexdigest()
    body={'schema':'multipanel_label_scenario_lease_issue_v2','manifest_hash':document['self_hash'],
          'manifest_file_hash':freeze_receipt['manifest_file_hash'],'transition_receipt_hash':transition_receipt['self_hash'],
          'token_hash':token_hash,'source_commit':manifest.source_commit}
    body={**body,'self_hash':_hash(body)};_publish_new(directory/'label-scenario-lease.issue.json',canonical_json_line_v2(body))
    return LabelScenarioLeaseV2(_LEASE_SENTINEL,token,document['self_hash'],body['self_hash'],directory)


def consume_label_scenario_lease_v2(lease:LabelScenarioLeaseV2,manifest:GlobalPredictionManifestV2,
                                    allowlists:Mapping[str,FrozenFeatureAllowlistAuthorityV2],reader:Callable[[],Any])->Any:
    if type(lease) is not LabelScenarioLeaseV2 or not callable(reader):raise MultiPanelCustodyError('valid opaque lease and reader required')
    manifest.validate(allowlists);document=manifest.document();directory=lease.directory
    issue_path=directory/'label-scenario-lease.issue.json'
    if not issue_path.is_file():raise MultiPanelCustodyError('durable lease issue missing')
    issue=json.loads(issue_path.read_text(encoding='utf-8'))
    if (issue.get('self_hash'),issue.get('manifest_hash'),issue.get('token_hash'))!=(lease.issue_receipt_hash,document['self_hash'],lease.token_hash()):
        raise MultiPanelCustodyError('lease authority mismatch')
    manifest_path=directory/'global_prediction_manifest_v2.json';before=sha256(manifest_path.read_bytes()).hexdigest()
    consumed={'schema':'multipanel_label_scenario_lease_consumed_v2','issue_receipt_hash':issue['self_hash'],
              'manifest_hash':document['self_hash'],'manifest_file_hash_before':before,'token_hash':lease.token_hash(),
              'source_commit':manifest.source_commit}
    consumed={**consumed,'self_hash':_hash(consumed)}
    _publish_new(directory/'label-scenario-lease.consumed.json',canonical_json_line_v2(consumed))
    try:
        result=reader()
    finally:
        after=sha256(manifest_path.read_bytes()).hexdigest()
        if after!=before:raise MultiPanelCustodyError('post-freeze manifest mutation')
    completed={'schema':'multipanel_label_scenario_lease_completion_v2','consumed_receipt_hash':consumed['self_hash'],
               'manifest_file_hash_after':after,'source_commit':manifest.source_commit}
    completed={**completed,'self_hash':_hash(completed)}
    _publish_new(directory/'label-scenario-lease.completed.json',canonical_json_line_v2(completed));return result


__all__=['GlobalPredictionStateV1','PredictionCellReceiptV1','GlobalPredictionManifestV1','LabelScenarioLeaseV1',
         'issue_label_scenario_lease_v1','consume_label_scenario_lease_v1','validate_attack_feature_projection_contract_v1',
         'project_attack_columns_v1','validate_state_transition_v1','MultiPanelCustodyError',
         'FROZEN_PANEL_ORDER_V2','PRIMARY_METHODS_V2','SECONDARY_METHODS_V2','FrozenFeatureAllowlistAuthorityV2',
         'AttackFeatureProjectionReceiptV2','MethodCellAuthorityV2','GlobalCellCensusAuthorityV2',
         'PredictionSuccessReceiptV2','PredictionFailureReceiptV2','GlobalPredictionManifestV2',
         'project_attack_columns_v2','canonical_projection_bytes_v2','persist_global_manifest_v2',
         'initialize_state_chain_v2','advance_state_chain_v2','validate_transition_receipt_v2',
         'LabelScenarioLeaseV2','issue_label_scenario_lease_v2','consume_label_scenario_lease_v2']
